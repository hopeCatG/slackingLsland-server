from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.chat_companion import router as chat_companion_router
from app.api.personality import router as personality_router
from app.api.storage import router as storage_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.response import error_response, success_response

settings = get_settings()
app = FastAPI(title=settings.app_name)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_allow_origins), allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_companion_router, prefix="/api/v1")
app.include_router(personality_router, prefix="/api/v1")
app.include_router(storage_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content=error_response("请求参数校验失败", 422, {"errors": exc.errors()}))


@app.exception_handler(HTTPException)
async def http_error(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=error_response(str(exc.detail), exc.status_code))


@app.exception_handler(Exception)
async def unknown_error(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=error_response("服务器内部错误", 500))


@app.get("/")
async def health() -> dict:
    return success_response({"message": "Slack-off API is running"})
