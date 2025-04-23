from fastapi import FastAPI, UploadFile, Form
from utils.base import TextRequest, SpeechRequest
from utils.model import TextModel, SpeechModel
import speech_recognition as sr
import tempfile
import uvicorn

app = FastAPI()


@app.post("/translate/audio")
async def translate_audio(request: SpeechRequest):
    model = SpeechModel()



@app.post("/translate/text")
async def translate_text(request: TextRequest):
    model = TextModel()
    return model.generate(request)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)