from uuid import uuid4
import inspect
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, Request
from dotenv import load_dotenv
from collections.abc import AsyncGenerator

from schema.base import UserInput, StreamInput
from langgraph.pregel import Pregel
from langgraph.types import Command, Interrupt
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, AIMessageChunk, AnyMessage, HumanMessage, ToolMessage
from typing import Any
from agents.agent import get_agent, get_all_agent_info, DEFAULT_AGENT
from backend.api.service.utils import langchain_to_chat_message
from logs.logger_factory import get_logger
import traceback

logger = get_logger("chat", "chat.log")


load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
        agents = get_all_agent_info()
        app.state.agent_pool = {}
        for info in agents:
            agent = get_agent(info.key)
            app.state.agent_pool[info.key] = agent
            print(f"✅ Preloaded {len(app.state.agent_pool)} agents.")

        yield
        app.state.agent_pool.clear()
        print("✅ Cleared agent pool.")
    except Exception as e:
        logger.exception("🔥 Error during lifespan setup")
        raise HTTPException(status_code=500, detail=str(e))

router = APIRouter(lifespan=lifespan)


async def _handle_input(user_input: UserInput, agent: Pregel):
    """
    """
    run_id = uuid4()
    thread_id = user_input.thread_id

    configurable = {
        "model": user_input.model,
        "thread_id": thread_id,
    }

    if user_input.agent_config:
        if overlap := configurable.keys() & user_input.agent_config.keys():
            raise HTTPException(
                status_code=422,
                detail=f"agent_config contains reserved keys: {overlap}",
            )
        configurable.update(user_input.agent_config)
    
    config = RunnableConfig(
        run_id=run_id,
        configurable=configurable,
    )

    state = await agent.aget_state(config=config)
    interrupted_tasks = [
        task for task in state.tasks if hasattr(task, "interrupts") and task.interrupts
    ]

    input: Command | dict[str, Any]
    if interrupted_tasks:
        # assume user input is response to resume agent execution from interrupt
        input = Command(resume=user_input.message)
    else:
        input = {"messages": [HumanMessage(content=user_input.message)]}


    kwargs = {
        "input": input,
        "config": config,
    }

    return kwargs, run_id

@router.post("/invoke")
async def invoke(request: Request, user_input: UserInput, agent_key: str = DEFAULT_AGENT):
    
    agent_pool = request.app.state.agent_pool
    agent: Pregel = agent_pool.get(agent_key)
    if agent is None:
      logger.warning(f"❌ Agent '{agent_key}' not found.")
      raise HTTPException(status_code=404, detail=f"Agent '{agent_key}' not found.")

    kwargs, run_id = await _handle_input(user_input, agent)
    try:
        response_events: list[tuple[str, Any]] = await agent.ainvoke(**kwargs, stream_mode=["updates", "values"])  # type: ignore # fmt: skip
        logger.info(f"✅ Agent returned events: {[event[0] for event in response_events]}")
        logger.info(f"🔍 Last event: {response_events[-1]}")

        response_type, response = response_events[-1]
        logger.info(f"🧠 messages = {response['messages']}")
        
        if response_type == "values":
            # Normal response, the agent completed successfully
            try:
              logger.debug(f"🧪 messages: {response['messages']}")
              output = langchain_to_chat_message(response["messages"][-1])

            except Exception as e:
                logger.exception("💥 Error converting response to chat message")
                raise HTTPException(status_code=500, detail="Error in message conversion")
            
        elif response_type == "updates" and "__interrupt__" in response:
            # The last thing to occur was an interrupt
            # Return the value of the first interrupt as an AIMessage
            output = langchain_to_chat_message(
                AIMessage(content=response["__interrupt__"][0].value)
            )
            
        else:
            logger.error(f"❌ Unexpected response type: {response_type}")
            raise ValueError(f"Unexpected response type: {response_type}")

        output.run_id = str(run_id)
        return output
   
    except Exception as e:
        logger.exception("🔥 Unexpected error during /invoke")
        raise HTTPException(status_code=500, detail="Unexpected error")


def _create_ai_message(parts: dict) -> AIMessage:
    sig = inspect.signature(AIMessage)
    valid_keys = set(sig.parameters)
    filtered = {k: v for k, v in parts.items() if k in valid_keys}
    # Ensure 'content' is always present
    if "content" not in filtered:
        logger.error("❌ AIMessage must have 'content' field")
        raise ValueError("AIMessage must have 'content' field")
    
    filtered["type"] = "ai"
    # Convert any message chunks to a single AIMessage
    return AIMessage(**filtered)


async def message_generator(request: Request,
    user_input: StreamInput, agent_key: str = DEFAULT_AGENT
) -> AsyncGenerator[str, None]:
    """
    Generate a stream of messages from the agent.

    This is the workhorse method for the /stream endpoint.
    """
    agent_pool = request.app.state.agent_pool
    agent: Pregel = agent_pool.get(agent_key)

    kwargs, run_id = await _handle_input(user_input, agent)

    try:
        # Process streamed events from the graph and yield messages over the SSE stream.
        async for stream_event in agent.astream(
            **kwargs, stream_mode=["updates", "messages"]
        ):
            logger.info(f"🔂 stream_event = {stream_event}")
            if not isinstance(stream_event, tuple):
                continue
            stream_mode, event = stream_event
            new_messages = []
            if stream_mode == "updates":
                for node, updates in event.items():
                    # A simple approach to handle agent interrupts.
                    # In a more sophisticated implementation, we could add
                    # some structured ChatMessage type to return the interrupt value.
                    if node == "__interrupt__":
                        interrupt: Interrupt
                        for interrupt in updates:
                            new_messages.append(AIMessage(content=interrupt.value))
                            logger.info(f"⚠️ Interrupt message: {msg.content[:80]}")
                        continue

                    updates = updates or {}
                    update_messages = updates.get("messages", [])
                    # special cases for using langgraph-supervisor library
                    if node == "supervisor":
                        # Get only the last AIMessage since supervisor includes all previous messages
                        ai_messages = [msg for msg in update_messages if isinstance(msg, AIMessage)]
                        if ai_messages:
                            update_messages = [ai_messages[-1]]
                    new_messages.extend(update_messages)
            processed_messages = []
            current_messages = {}

            for msg in new_messages:
                if isinstance(msg, tuple):
                    key, value = msg
                    current_messages[key] = value
                else:
                    if current_messages:
                        processed_messages.append(_create_ai_message(current_messages))
            
            if current_messages:
                processed_messages.append(_create_ai_message(current_messages))
            
            for msg in processed_messages:
                try:
                    logger.info(f"🔎 Converting msg to chat: {msg}")
                    chat_message = langchain_to_chat_message(msg)

                    chat_message.run_id = str(run_id)

                    logger.info(f"🟢 Yielding chat message: {chat_message.content[:100]}")
                    yield f"data: {json.dumps({'type': 'message', 'content': chat_message.dict()})}\n\n"

                except Exception as e:
                    logger.exception("💥 Error converting message to ChatMessage")
                    yield f"data: {json.dumps({'type': 'error', 'content': 'Internal server error'})}\n\n"
                    continue

                yield f"data: {json.dumps({'type': 'message', 'content': chat_message.model_dump()})}\n\n"

            if stream_mode == "messages":
                logger.info(f"🔁 stream_mode={stream_mode}, event={event}")
                if not user_input.stream_tokens:
                    continue

                msg, metadata = event
                if not isinstance(msg, AIMessageChunk):
                    logger.warning("⚠️ Skipped non-AIMessageChunk in stream_mode=messages")
                    continue

                # Convert the message to a standard AIMessage
                ai_message = _create_ai_message(msg.dict())

                ai_message.run_id = str(run_id)
                ai_message.metadata = metadata
                
                logger.info(f"🟢 Yielding token chunk: {ai_message.content[:50]}")
                token = ai_message.content

                if token.strip() == "":
                    logger.warning("⚠️ Skipped empty token chunk")
                    continue

                logger.info(f"🟢 Yielding token chunk: {token[:50]}")
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"🔥 Error in message_generator: {e}")
        logger.error(tb)
        
        yield f"data: {json.dumps({'type': 'error', 'content': 'Internal server error'})}\n\n"
    finally:
        yield "data: [DONE]\n\n"


@router.post("/stream", response_class=StreamingResponse)
async def stream(request: Request, user_input: StreamInput, agent_key: str = DEFAULT_AGENT) -> StreamingResponse:
    """
    Stream an agent's response to a user input, including intermediate messages and tokens.

    If agent_id is not provided, the default agent will be used.
    Use thread_id to persist and continue a multi-turn conversation. run_id kwarg
    is also attached to all messages for recording feedback.
    Use user_id to persist and continue a conversation across multiple threads.

    Set `stream_tokens=false` to return intermediate messages but not token-by-token.
    """
    return StreamingResponse(
        message_generator(request, user_input, agent_key),
        media_type="text/event-stream",
    )