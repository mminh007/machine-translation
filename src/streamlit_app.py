import streamlit as st
import requests
import tempfile
import uuid
from client import AgentClient, AgentClientError
from audio_recorder_streamlit import audio_recorder
import os
import asyncio

from typing import AsyncGenerator
from schema.base import ChatMessage, ChatHistory
from logs.logger_factory import get_logger
import traceback

logger = get_logger("streamlit", "streamlit.log")


def get_or_create_user_id():
    if "user_id" in st.session_state:
        return st.session_state['user_id']

    user_id = str(uuid.uuid4())
    st.session_state['user_id'] = user_id

    st.query_params["user_id"] = user_id

    return user_id


async def main():
    user_id = get_or_create_user_id()

    st.set_page_config(page_title="Audio Translation App", page_icon=":microphone:")
    st.title("🤖 Machine Translation App")
    st.write("This app translates audio or text from Vietnamese to English and vice versa.")

    with st.sidebar:
        st.title("Text - Audio Translation")
        st.write("Select source translation:")
        
        data_input = st.radio("Input Type", [" ✍️ Text", "🤖 Chatbot"])
        
       
    
    if data_input == "🤖 Chatbot":
        st.title("🤖 Chatbot")
        st.write("This app translates audio or text from Vietnamese to English and vice versa.")

        with st.sidebar:
            if st.button("New Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.thread_id = str(uuid.uuid4())
                st.rerun()
            
            use_streaming = st.toggle("Use Streaming", value=True)
        
        if "agent_client" not in st.session_state:
            agent_url = "http://backend:8000"
            try:
                with st.spinner("Connecting to agent service..."):
                    st.session_state.agent_client = AgentClient(base_url=agent_url)

            except AgentClientError as e:
                tb = traceback.format_exc()
                logger.error(f"🔌 Agent connection failed: {e}\n{tb}")
                st.error(f"Error connecting to agent service at {agent_url}: {e}")
                st.markdown("The service might be booting up. Try again in a few seconds.")
                st.stop()
                    
        agent_client: AgentClient = st.session_state.agent_client

        if "thread_id" not in st.session_state:
            thread_id = st.query_params.get("thread_id", None)
            if thread_id is None:
                thread_id = str(uuid.uuid4())
                messages = []
            else:
                try:
                    messages: ChatHistory = agent_client.get_history(thread_id=thread_id).messages
                    logger.info(f"📜 Loaded history for thread_id={thread_id} with {len(messages)} messages")

                except AgentClientError:
                    tb = traceback.format_exc()
                    logger.warning(f"⚠️ No message history for thread_id={thread_id}: {e}\n{tb}")
                    st.error("No message history found for this Thread ID.")
                    messages = []

            st.session_state.thread_id = thread_id
            st.session_state.messages = messages

        if "recorded_text" not in st.session_state:
            st.session_state.recorded_text = ""

        if not st.session_state.messages:
            st.chat_message("ai").write("🎤 Press the microphone to speak and start the conversation.")
        
        for msg in st.session_state.messages:
            with st.chat_message(msg.type):
                st.write(msg.content)
        
        with st.form("Send"):
            col1, col2 = st.columns([9, 1])
            with col1:
                usr_input = st.text_input("", key="audio_input")
            with col2:
                audio_bytes = audio_recorder(text="", icon_size="2x", icon_name="microphone")
            submitted = st.form_submit_button("Send")

        if audio_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                f.write(audio_bytes)
                audio_path = f.name

            with open(audio_path, "rb") as f:
                res = requests.post("http://backend:8000/speech2text/audio", files={"audio_file": f})
                if res.ok:
                    st.session_state["recorded_text"] = res.json()["text"]
                else:
                    logger.error(f"❌ Voice recognition failed: {res.status_code} - {res.text}")
                    st.error("❌ Voice recognition failed.")
            os.remove(audio_path)

        if submitted and usr_input.strip() != "":
            st.session_state.recorded_text = ""

            st.session_state.messages.append(ChatMessage(type="human", content=usr_input))
            msg = ChatMessage(type="human", content=usr_input)
            with st.chat_message(msg.type):
                st.write(msg.content)

            try:
                if use_streaming:
                    logger.info(f"🧠 Sending streaming request to backend with input: {usr_input}")
                    stream = agent_client.astream(
                        message=usr_input,
                        model="llama-32-1B-instruct",
                        thread_id=st.session_state.thread_id,
                        user_id=user_id,
                        agent_config={},
                    )
                    logger.info(f"🧠 Response from backend: {stream}")

                    if not stream:
                        logger.warning("⚠️ Backend returned empty or invalid response")
                        st.warning("No response received from backend.")
                    else:
                        logger.info("🧠 Streaming response from backend...")
                        await draw_streaming_response(stream, is_new=True)

                else:
                    logger.info(f"🧠 Sending ainvoke request to backend with input: {usr_input}")
                    response = await agent_client.ainvoke(
                        message=usr_input,
                        model="llama-32-1B-instruct",
                        thread_id=st.session_state.thread_id,
                        user_id=user_id,
                        agent_config={},
                    )
                    logger.info(f"🧠 Response from backend: {response}")

                    if not response or "content" not in response:
                        logger.warning("⚠️ Backend returned empty or invalid response")
                        st.warning("No response received from backend.")
                    else:
                        st.session_state.messages.append(ChatMessage(type="ai", content=response["content"]))
                        with st.chat_message("ai"):
                            st.write(response["content"])
                st.rerun()

            except Exception as e:
                tb = traceback.format_exc()
                logger.error(f"🔥 Error while processing agent response: {e}\n{tb}")
                st.error(f"❌ Error: {e}")
                st.stop()

    else:
        st.title("✍️ Text Translation")

        with st.sidebar:           
            src_lang = st.selectbox("Source Language", ["en_XX", "vi_VN", "fr_XX", "de_DE", "es_XX", "ru_RU", "zh_CN", "ja_XX"])
            tgt_lang = st.selectbox("Target Language", ["en_XX", "vi_VN", "fr_XX", "de_DE", "es_XX", "ru_RU", "zh_CN", "ja_XX"])
            model = st.selectbox("Model", ["google/T5", "facebook/Mbart50"])

            if st.button("New Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.thread_id = str(uuid.uuid4())
                st.rerun()

        if "thread_id" not in st.session_state:
            thread_id = st.query_params.get("thread_id", None)
            if thread_id is None:
                thread_id = str(uuid.uuid4())
                messages = []
            st.session_state.thread_id = thread_id
            st.session_state.messages = messages
        
        for msg in st.session_state.messages:
            with st.chat_message(msg.type):
                st.write(msg.content)

        # text_input = st.text_area("Enter text to translate")
        if user_input := st.chat_input():
            st.session_state.messages.append(ChatMessage(type="human", content=user_input))
            with st.chat_message(msg.type):
                st.write(msg.content)

            try:
                # Call the backend API for translation
                response = requests.post(
                    "http://backend:8000/speech2text/text",
                    json={"text": user_input, "src_lang": src_lang, "tgt_lang": tgt_lang, "model": model},
                )

                data = response.json()
                if response.status_code == 200 and "text" in data:                   
                    st.session_state.messages.append(ChatMessage(type="ai", content=data["text"]))
                    with st.chat_message("ai"):
                        st.write(data["text"])

                else:
                    st.write(data["error"])
                    logger.error(f"❌ Translation error: {data.get('error')}")
                    st.error(f"❌ Error: {response.json()}")
                
                # st.rerun()
            except requests.exceptions.RequestException as e:
                tb = traceback.format_exc()
                logger.error(f"🌐 Translation request failed: {e}\n{tb}")
                st.error(f"❌ Error: {e}")
    
async def draw_streaming_response(
    messages_agen: AsyncGenerator[ChatMessage | str, None],
    is_new: bool = False) -> None:
    """
    Draws a set of chat messages - either replaying existing messages
    or streaming new ones.

    This function has additional logic to handle streaming tokens and tool calls.
    - Use a placeholder container to render streaming tokens as they arrive.
    - Use a status container to render tool calls. Track the tool inputs and outputs
    and update the status container accordingly.

    The function also needs to track the last message container in session state
    since later messages can draw to the same container. This is also used for
    drawing the feedback widget in the latest chat message.

    Args:
        messages_aiter: An async iterator over messages to draw.
        is_new: Whether the messages are new or not.
    """

    # Keep track of the last message container
    last_message_type = None
    st.session_state.last_message = None

    # Placeholder for intermediate streaming tokens
    streaming_content = ""
    streaming_placeholder = None

    # Iterate over the messages and draw them
    while msg := await anext(messages_agen, None):
        if msg is None or (isinstance(msg, str) and msg.strip() == ""):
            continue  # Skip empty or None tokens
        
        # str message represents an intermediate token being streamed
        logger.info(f"📥 Received stream token: {msg}")
        if isinstance(msg, str):
            # If placeholder is empty, this is the first token of a new message
            # being streamed. We need to do setup.
            if not streaming_placeholder:
                if last_message_type != "ai":
                    last_message_type = "ai"
                    st.session_state.last_message = st.chat_message("ai")
                with st.session_state.last_message:
                    streaming_placeholder = st.empty()

            streaming_content += msg
            streaming_placeholder.write(streaming_content)
            continue
        if not isinstance(msg, ChatMessage):
            st.error(f"Unexpected message type: {type(msg)}")
            st.write(msg)
            st.stop()

        match msg.type:
            # A message from the user, the easiest case
            case "human":
                last_message_type = "human"
                with st.chat_message(msg.type):
                    st.write(msg.content)
                #st.chat_message("human").write(msg.content)

            # A message from the agent is the most complex case, since we need to
            # handle streaming tokens and tool calls.
            case "ai":
                # If we're rendering new messages, store the message in session state
                if is_new:
                    st.session_state.messages.append(msg)

                # If the last message type was not AI, create a new chat message
                if last_message_type != "ai":
                    last_message_type = "ai"
                    st.session_state.last_message = st.chat_message("ai")

                with st.session_state.last_message:
                    # If the message has content, write it out.
                    # Reset the streaming variables to prepare for the next message.
                    if msg.content:
                        if streaming_placeholder:
                            streaming_placeholder.write(msg.content)
                            streaming_content = ""
                            streaming_placeholder = None
                        else:
                            st.write(msg.content)

                    # if msg.tool_calls:
                    #     # Create a status container for each tool call and store the
                    #     # status container by ID to ensure results are mapped to the
                    #     # correct status container.
                    #     call_results = {}
                    #     for tool_call in msg.tool_calls:
                    #         status = st.status(
                    #             f"""Tool Call: {tool_call["name"]}""",
                    #             state="running" if is_new else "complete",
                    #         )
                    #         call_results[tool_call["id"]] = status
                    #         status.write("Input:")
                    #         status.write(tool_call["args"])

                    #     # Expect one ToolMessage for each tool call.
                    #     for _ in range(len(call_results)):
                    #         tool_result: ChatMessage = await anext(messages_agen)

                    #         if tool_result.type != "tool":
                    #             st.error(f"Unexpected ChatMessage type: {tool_result.type}")
                    #             st.write(tool_result)
                    #             st.stop()

                    #         # Record the message if it's new, and update the correct
                    #         # status container with the result
                    #         if is_new:
                    #             st.session_state.messages.append(tool_result)
                    #         if tool_result.tool_call_id:
                    #             status = call_results[tool_result.tool_call_id]
                    #         status.write("Output:")
                    #         status.write(tool_result.content)
                    #         status.update(state="complete")

            # In case of an unexpected message type, log an error and stop
            case _:
                st.error(f"Unexpected ChatMessage type: {msg.type}")
                st.write(msg)
                st.stop()
    
    if streaming_content:
        if streaming_placeholder:
            streaming_placeholder.write(streaming_content)
        if is_new:
            st.session_state.messages.append(ChatMessage(type="ai", content=streaming_content))

if __name__ == "__main__":
    asyncio.run(main())
                    




    # if data_input == "🎤 Audio":
    #     st.title("🎤 Audio Translation")

    #     with st.chat_message("user"):
    #         st.write("Audio recorded successfully!")
       
    #     col1, col2 = st.columns([9, 1])

    #     with col1:
    #         st.chat_input("Press to record audio", key="audio_input")
    #     with col2:
    #         audio_bytes = audio_recorder(text="", icon_size="2x", icon_name="microphone")