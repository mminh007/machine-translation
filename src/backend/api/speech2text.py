from fastapi import Request, UploadFile, File, APIRouter, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from schema.base import SpeechRequest
from schema.models import SpeechModel
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from logs.logger_factory import get_logger

logger = get_logger("speech2text", "speech2text.log")
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    try:
       app.state.speech_model = SpeechModel()
       yield
       app.state.speech_model = None
    except Exception as e:
        logger.exception(f"🔥 Error during audio translation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


router = APIRouter(lifespan=lifespan)

@router.post("/audio")
async def translate_audio(request: Request, audio_file: UploadFile = File(...)):
  try:
    contents = await audio_file.read()
    speech_request = SpeechRequest(
      audio=contents
    )
    model = request.app.state.speech_model
    return model.generate(speech_request)

  except Exception as e:
    logger.exception(f"🔥 Error during audio translation: {e}")
    return JSONResponse(status_code=500, content={"error": str(e)})


# @router.post("/translate/text")
# async def translate_text(request: TextRequest):
#     try:
#         model = TextModel()
#         return model.generate(request)
    
#     except Exception as e:
#         print(f"🔥 Backend Error: {str(e)}")
#         return JSONResponse(status_code=500, content={"error": str(e)})

