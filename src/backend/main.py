from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback

from backend.api.chat import router as chat_router
from backend.api.speech2text import router as speech2text_router
from logs.logger_factory import get_logger
import traceback  
import uvicorn

logger = get_logger("FastAPI", "backend.log")

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cẩn thận khi đưa vào production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Middleware log 
@app.middleware("http")
async def log_requests(request: Request, call_next):
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            body = await request.body()
            logger.warning(f"❌ {request.method} {request.url} returned {response.status_code}")
            logger.warning(f"Request body: {body.decode('utf-8')}")
        return response
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"🔥 Exception in request: {request.method} {request.url}")
        logger.error(tb)
        raise e

# ✅ Handler System Error (Exception)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error(f"🔥 Unhandled Exception: {exc}")
    logger.error(tb)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "details": str(exc)},
    )

# ✅ Handler  HTTP Error (detail)  (ex 404, 422)
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    logger.warning(f"⚠️ HTTP Exception: {exc.status_code} - {exc.detail}")
    return await http_exception_handler(request, exc)

# ✅ Handler validation Error (Pydantic)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"🛑 Validation Error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body": exc.body},
    )

# ✅ router
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(speech2text_router, prefix="/speech2text", tags=["speech2text"])

# ✅ app
if __name__ == "__main__":
    logger.info("🚀 Starting FastAPI server...")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
