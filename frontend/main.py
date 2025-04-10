import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import requests
import av
import os
import uuid
import wave
import tempfile

# import sounddevice as sd
# import wavio
# import wave

# def record_audio(filename="recorded.wav", duration=5, fs=44100):
#     print("🎤 Start to record...")
#     recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
#     sd.wait()
#     wavio.write(filename, recording, fs, sampwidth=2)
#     print("🎤 Final Record!")
#     return filename
if __name__ == "__main__":
    st.title("Audio Translation App")
    st.write("This app translates audio or text from Vietnamese to English and vice versa.")

    with st.sidebar:
        st.title("Audio Translation")
        st.write("Select source and target languages for translation.")
        src_lang = st.selectbox("Source Language", ["en_US", "vi_VN"])
        tgt_lang = st.selectbox("Target Language", ["en_US", "vi_VN"])
        st.write("Audio or Text Input")
        audio_input = st.radio("Input Type", ["Audio", "Text"])


    if audio_input == "Audio":
        st.title("Audio Input Recorder")
        webrtc_ctx = webrtc_streamer(
            key="audio",
            mode=WebRtcMode.SENDRECV,
            audio_receiver_size=256,
            media_stream_constraints={"audio": True, "video": False},
        )

        if st.button("Translate"):
            if webrtc_ctx.audio_receiver:
                audio_frames = webrtc_ctx.audio_receiver.get_frames()
                audio_data = b"".join([frame.to_ndarray().tobytes() for frame in audio_frames])
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_data)
                    tmp_path = tmp.name

                # Call the backend API for translation
                with open(tmp_path, "rb") as f:
                    response = requests.post(
                        "http://localhost:8000/translate/audio",
                        files={"audio": f},
                        data={"src_lang": src_lang, "tgt_lang": tgt_lang},
                    )
                os.remove(tmp_path)

                if response.status_code == 200:
                    result = response.json()
                    st.success(f"Transcript: {result['transcript']}")
                    st.success(f"Translation: {result['translation']}")
                else:
                    st.error("Error in translation")
            else:
                st.error("No audio input detected. Please record audio.")

    else:
        st.title("Text Input")

        text_input = st.text_area("Enter text to translate")

        if st.button("Translate"):
            # Call the backend API for translation
            response = requests.post(
                "http://localhost:8000/translate/text",
                data={"text": text_input, "src_lang": src_lang, "tgt_lang": tgt_lang},
            )

            if response.status_code == 200:
                result = response.json()
                st.success(f"Translation: {result['translation']}")
            else:
                st.error("Error in translation")








    # st.title("Audio Input Recorder")

    #     # WebRTC configuration
    #     st.subheader("Record Audio")
    #     webrtc_streamer(
    #         key="audio-recorder",
    #         mode=WebRtcMode.SENDONLY,
    #         audio_receiver_size=256,
    #     )

    #     # Temporary file to store audio
    #     temp_dir = tempfile.gettempdir()
    #     audio_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.wav")

    #     # Save audio to .wav file
    #     def save_audio_to_file(audio_frames, file_path):
    #         with wave.open(file_path, "wb") as wf:
    #             wf.setnchannels(1)  # Mono audio
    #             wf.setsampwidth(2)  # Sample width in bytes
    #             wf.setframerate(44100)  # Frame rate
    #             wf.writeframes(b"".join(audio_frames))

    #     st.write("Use the above widget to record audio from your microphone.")

    #     # Example usage: Save dummy audio frames (replace with actual frames from WebRTC)
    #     dummy_audio_frames = [b"\x00\x00" * 44100]  # 1 second of silence
    #     save_audio_to_file(dummy_audio_frames, audio_file_path)

    #     st.write(f"Audio saved to: {audio_file_path}")