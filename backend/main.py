from fastapi import FastAPI, UploadFile, Form
from pydantic import BaseModel
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast
import speech_recognition as sr
import tempfile
import uvicorn

app = FastAPI()

# Load model
model_name = "facebook/mbart-large-50-many-to-many-mmt"
print("Loading model...")
tokenizer = MBart50TokenizerFast.from_pretrained(model_name)
model = MBartForConditionalGeneration.from_pretrained(model_name)
print("Model loaded.")

@app.post("/translate/audio")
async def translate_audio(audio: UploadFile, src_lang: str = Form(...), tgt_lang: str = Form(...)):
    if src_lang not in tokenizer.lang_code_to_id or tgt_lang not in tokenizer.lang_code_to_id:
        return {"error": "Unsupported language code."}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    recognizer = sr.Recognizer()
    with sr.AudioFile(tmp_path) as source:
        audio_data = recognizer.record(source)
        try:
            language_code = "vi-VN" if src_lang == "vi_VN" else "en-US"
            transcript = recognizer.recognize_google(audio_data, language=language_code)
        except Exception as e:
            return {"error": str(e)}

    tokenizer.src_lang = src_lang
    encoded = tokenizer(transcript, return_tensors="pt")
    generated = model.generate(
        **encoded,
        forced_bos_token_id=tokenizer.lang_code_to_id[tgt_lang]
    )
    translation = tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
    return {"transcript": transcript, "translation": translation}


@app.post("/translate/text")
async def translate_text(text: str = Form(...), src_lang: str = Form(...), tgt_lang: str = Form(...)):
    if src_lang not in tokenizer.lang_code_to_id or tgt_lang not in tokenizer.lang_code_to_id:
        return {"error": "Unsupported language code."}

    tokenizer.src_lang = src_lang
    encoded = tokenizer(text, return_tensors="pt")
    generated = model.generate(
        **encoded,
        forced_bos_token_id=tokenizer.lang_code_to_id[tgt_lang]
    )
    translation = tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
    return {"translation": translation}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)