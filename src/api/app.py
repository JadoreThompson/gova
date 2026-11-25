from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.exception import ExceptionHandlerMiddleware
from auth.router import router as auth_router
from config import (
    APP_ALLOW_CREDENTIALS,
    APP_ALLOWED_HEADERS,
    APP_ALLOWED_METHODS,
    APP_ALLOWED_ORIGINS,
)
from moderator.router import router as moderator_router
from user.router import router as user_router

app = FastAPI(title="Gova API")

# Middlewares
# app.add_middleware(ExceptionHandlerMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=APP_ALLOWED_ORIGINS,
    allow_headers=APP_ALLOWED_HEADERS,
    allow_methods=APP_ALLOWED_METHODS,
    allow_credentials=APP_ALLOW_CREDENTIALS,
)

# Routers
app.include_router(auth_router)
app.include_router(moderator_router)
app.include_router(user_router)
