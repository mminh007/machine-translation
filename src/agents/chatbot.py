from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.func import entrypoint

from core import get_model, settings
from logs.logger_factory import get_logger
import traceback

logger = get_logger("chatbot-agent", 'chatbot-agent.log')

@entrypoint(checkpointer=MemorySaver())
async def chatbot(
    inputs: dict[str, list[BaseMessage]],
    *,
    previous: dict[str, list[BaseMessage]],
    config: RunnableConfig,
):
    try:
        messages = inputs["messages"]
        if previous:
            messages = previous["messages"] + messages

        model_name = config["configurable"].get("model", settings.DEFAULT_MODEL)
        logger.debug(f"🧠 Requested model: {model_name}")
        logger.debug(f"📦 Full config received: {config}")

        model = get_model(model_name)

        if model is None:
            logger.error(f"❌ get_model() returned None for model: {model_name}")
            raise ValueError(f"Invalid or unsupported model: {model_name}")

        response = await model.ainvoke(messages)

        return entrypoint.final(
            value={"messages": [response]},
            save={"messages": messages + [response]},
        )

    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"🔥 Error in chatbot agent: {e}\n{tb}")
        raise