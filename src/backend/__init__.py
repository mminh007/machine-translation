from fastapi import APIRouter
from backend.api.chat import router as chat_router
from backend.api.speech2text import router as speech2text_router

router = APIRouter()
@router.get("/")
async def root():
    return {"message": "Welcome to the Machine Translator API!"}

@router.get("/health")
async def health_check():
    return {"status": "ok"}

router.include_router(chat_router, prefix="/chat", tags=["chat"])
router.include_router(speech2text_router, prefix="/speech2text", tags=["speech2text"])