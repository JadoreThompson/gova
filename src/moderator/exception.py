from fastapi import HTTPException, status

from core.exception import ExceptionHandler


class ModeratorNotFoundException(Exception):
    def __init__(self):
        super().__init__("Moderator not found")


class ModeratorExceptionHandler(ExceptionHandler):
    exceptions = {
        ModeratorNotFoundException: HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderator not found",
        ),
    }
