from fastapi import HTTPException, status

from core.exception import ExceptionHandler
from security.jwt.exception import JWTException


class InvalidCredentialsException(Exception):
    def __init__(self):
        super().__init__("Invalid credentials")


class AuthExceptionHandler(ExceptionHandler):
    exceptions = {
        InvalidCredentialsException: HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ),
        JWTException: HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ),
    }
