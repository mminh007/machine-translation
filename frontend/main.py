import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import requests
import os
import tempfile


if __name__ == "__main__":
    st.set_page_config(page_title="Audio Translation App", page_icon=":microphone:")
    st.title("Audio Translation App")
    st.write("This app translates audio or text from Vietnamese to English and vice versa.")

    with st.sidebar:
        st.title("Audio Translation")
        st.write("Select source and target languages for translation.")
        src_lang = st.selectbox("Source Language", ["en_XX", "vi_VN"])
        tgt_lang = st.selectbox("Target Language", ["en_XX", "vi_VN"])
        st.write("Audio or Text Input")
        audio_input = st.radio("Input Type", ["Audio", "Text"])


    if audio_input == "Audio":
       pass

    else:
        st.title("Text Input")

        text_input = st.text_area("Enter text to translate")

        if st.button("Translate"):
            # Call the backend API for translation
            response = requests.post(
                "http://localhost:8000/translate/text",
                json={"text": text_input, "src_lang": src_lang, "tgt_lang": tgt_lang},
            )

            if response.status_code == 200:
                result = response.json()

                st.success(f"Translation: {result['translation']}")
            else:
                st.error("Error in translation")

