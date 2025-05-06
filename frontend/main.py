import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, AudioProcessorBase
import requests
import tempfile
import av
import wave
import numpy as np
import torchaudio
import torch
import uuid


torchaudio.set_audio_backend("soundfile")


if __name__ == "__main__":
    st.set_page_config(page_title="Audio Translation App", page_icon=":microphone:")
    st.title("🤖 Machine Translation App")
    st.write("This app translates audio or text from Vietnamese to English and vice versa.")

    with st.sidebar:
        st.title("Text - Audio Translation")
        st.write("Select source translation:")
        
        data_input = st.radio("Input Type", ["🎤 Audio", " ✍️ Text"])


    if data_input == "🎤 Audio":
        st.title("🎤 Audio Translation")
        with st.sidebar:
            tgt_lang = st.selectbox("Target Language", ["en", "vi", "fr", "de", "es", "ru", "zh", "ja"])
            task = st.selectbox("Task", ["transcribe", "translate"])
        class AudioProcessor(AudioProcessorBase):
            def __init__(self):
                self.audio_data = []

            def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
                audio_array = frame.to_ndarray()
                self.audio_data.append(audio_array)
                return frame
            

        ctx = webrtc_streamer(
            key="audio",
            mode=WebRtcMode.SENDRECV,
            audio_processor_factory=AudioProcessor,
            media_stream_constraints={"audio": True, "video": False},
        )

        def save_audio_with_wave(audio_data, sample_rate, output_path):
            if audio_data.ndim == 1:
                nchannels = 1
            else:
                nchannels = audio_data.shape[0]
                audio_data = audio_data.T  # (samples, channels)

            if audio_data.dtype != np.int16:
                audio_data = (audio_data * 32767).astype(np.int16)

            with wave.open(output_path, 'wb') as wf:
                wf.setnchannels(nchannels)
                wf.setsampwidth(2)  # 2 bytes = 16 bits
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data.tobytes())


        if st.button("Translate"):
            st.info("Processing audio...")
            processor = ctx.audio_processor

            if processor is None or not processor.audio_data:
                st.error("❌ No audio data received.")

            else:
                st.info("Processing audio...")
            
                audio_data = np.concatenate(processor.audio_data, axis=1)  # (channels, samples)
                sample_rate = 48000

                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                    torchaudio.save(tmpfile.name, torch.from_numpy(audio_data), sample_rate)
                    wav_path = tmpfile.name

                waveform, sr = torchaudio.load(wav_path)
                st.audio(wav_path, format="audio/wav")
                st.write(f"Waveform shape: {waveform.shape}, Sample rate: {sr}")

                st.write(f"Audio saved to: {wav_path}")
                st.write(f"Audio shape: {audio_data.shape}, Sample rate: {sample_rate}")

                    # Call the backend API for translation
                with open(wav_path, "rb") as f:
                    response = requests.post(
                        "http://localhost:8000/translate/audio",
                        files={"audio": ("recording.wav", f, "audio/wav"),
                            "task": task,
                            "tgt_lang": tgt_lang})
                        
                if response.status_code == 200:
                    result = response.json()
                    st.success(f"Translation: {result['translation']}")
                else:
                    st.error("❌ Error in translation")
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
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

        # text_input = st.text_area("Enter text to translate")
        if user_input := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.write(user_input)

            try:
                # Call the backend API for translation
                response = requests.post(
                    "http://localhost:8000/translate/text",
                    json={"text": user_input, "src_lang": src_lang, "tgt_lang": tgt_lang, "model": model},
                )

                if response.status_code == 200:
                    result = response.json()
                    st.session_state.messages.append({"role": "assistant", "content": result["translation"]})
                    with st.chat_message("ai"):
                        st.write(result["translation"])

                else:
                    st.error(f"❌ Error: {response.json()}")
                
                # st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Error: {e}")
                    

