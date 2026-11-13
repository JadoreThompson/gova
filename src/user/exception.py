from fastapi import HTTPException, status

from core.exception import ExceptionHandler


class UserNotFoundException(Exception):
    def __init__(self):
        super().__init__("User not found")


class UserAlreadyExistsException(Exception):
    def __init__(self):
        super().__init__("User already exists")


class UserExceptionHandler(ExceptionHandler):
    exceptions = {
        UserNotFoundException: HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ),
        UserAlreadyExistsException: HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        ),
    }
