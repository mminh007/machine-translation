import streamlit as st
from streamlit_float import *
import requests
import tempfile
import uuid
from client import AgentClient, AgentClientError, text_to_speech
from audio_recorder_streamlit import audio_recorder
import os
import asyncio

from typing import AsyncGenerator
from schema.base import ChatMessage, ChatHistory
from logs.logger_factory import get_logger
import traceback
import base64

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
        model = st.selectbox("LLM to use", options=["llama-32-1B-instruct", "gpt-4o-mini"])
        
       
    
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
            
        # voice
        if "recorded_text" not in st.session_state:
            st.session_state.recorded_text = ""

        if "processing" not in st.session_state:
            st.session_state.processing = ""
        
        if "use_voice" not in st.session_state:
            st.session_state.use_voice = False

        if not st.session_state.messages:
            st.chat_message("ai").write("🎤 Press the microphone to speak and start the conversation.")
        
        for msg in st.session_state.messages:
            with st.chat_message(msg.type):
                st.write(msg.content)       

        footer_container = st.container()
        with footer_container:
            audio_bytes = audio_recorder("", icon_size="2x", icon_name="microphone")


        chat_cont = st.container()
        with chat_cont:
            usr_input = st.chat_input("Your message")

        footer_container.float("bottom: 0.5rem; right: -15rem")
        chat_cont.float("bottom: 1rem; left: 47rem")

        if audio_bytes:
            audio_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
                    f.write(audio_bytes)
                    audio_path = f.name
                
                with open(audio_path, "rb") as f:
                    res = requests.post("http://backend:8000/speech2text/audio", files={"audio_file": f})
                    if res.ok:
                        st.session_state["recorded_text"] = res.json()["text"]
                        logger.info(f"🎤 Audio to text: {st.session_state['recorded_text']}")
                    else:
                        logger.error(f"❌ Voice recognition failed: {res.status_code} - {res.text}")
                        st.error("❌ Voice recognition failed.")
            finally:
                if audio_path and os.path.exists(audio_path):
                    try:
                        os.remove(audio_path)
                        logger.info(f"🗑️ Deleted temp file audio_path: {audio_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not delete temp file: {audio_path}. Reason: {e}")
        
        if st.session_state.recorded_text != "":
            st.session_state.messages.append(ChatMessage(type="human", content=st.session_state["recorded_text"]))
            st.session_state.processing = st.session_state["recorded_text"]
            st.session_state.recorded_text = ""
            st.session_state.use_voice = True
            
        if usr_input and usr_input != "":
            st.session_state.messages.append(ChatMessage(type="human", content=usr_input))
            st.session_state.processing = usr_input

        if st.session_state.processing != "":
            msg = st.session_state.messages[-1].content
            with st.chat_message("human"):
                st.write(msg)

            st.session_state.processing = ""

            try:
                if use_streaming:
                    logger.info(f"🧠 Sending streaming request to backend with input: {msg}")
                    stream = agent_client.astream(
                        message=msg,
                        model=model,
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
                    logger.info(f"🧠 Sending ainvoke request to backend with input: {msg}")
                    response = await agent_client.ainvoke(
                        message=msg,
                        model=model,
                        thread_id=st.session_state.thread_id,
                        user_id=user_id,
                        agent_config={},
                    )
                    logger.info(f"🧠 Response from backend: {response}")

                    if not response or "content" not in response:
                        logger.warning("⚠️ Backend returned empty or invalid response")
                        st.warning("No response received from backend.")

                    else:
                        if st.session_state.use_voice == True:
                            audio_file = text_to_speech(response["content"])
                            autoplay_audio(audio_file)
                            st.session_state.use_voice = False
                            
                            os.remove(audio_file)

                        st.session_state.messages.append(ChatMessage(type="ai", content=response["content"]))
                        with st.chat_message("ai"):
                            st.write(response["content"])    
                        
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
            model = st.selectbox("Model", ["facebook/Mbart50"])

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
            msg = ChatMessage(type="human", content=user_input)
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
                    msg = ChatMessage(type="ai", content=data["text"])
                    with st.chat_message(msg.type):
                        st.write(msg.content)

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

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    md = f"""
    <audio autoplay>
    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

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