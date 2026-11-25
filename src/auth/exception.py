from fastapi import HTTPException, status

from core.exception import ExceptionHandler
from security.jwt.exception import JWTException


class InvalidCredentialsException(Exception):
    def __init__(self):
        super().__init__("Invalid credentials")


class TwitchOAuthException(Exception):
    def __init__(self, message: str = "Failed to exchange Twitch authorization code"):
        super().__init__(message)


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
        TwitchOAuthException: HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to exchange Twitch authorization code",
        ),
    }
