from fastapi import HTTPException, status

from core.exception import ExceptionHandler


class ModeratorNotFoundException(Exception):
    def __init__(self):
        super().__init__("Moderator not found")


class ModeratorAlreadyExistsException(Exception):
    def __init__(self):
        super().__init__("Moderator already exists for this community")


class ModeratorWorkerNotFoundException(Exception):
    def __init__(self):
        super().__init__("Moderator worker not found")


class ModeratorWorkerAssignmentNotFoundException(Exception):
    def __init__(self):
        super().__init__("Moderator worker assignment not found")


class ModeratorAlreadyAssignedException(Exception):
    def __init__(self):
        super().__init__("Moderator is already assigned to a worker")


class NoAvailableModeratorWorkerException(Exception):
    def __init__(self):
        super().__init__("No moderator worker has available capacity")


class ModeratorExceptionHandler(ExceptionHandler):
    exceptions = {
        ModeratorNotFoundException: HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderator not found",
        ),
        ModeratorAlreadyExistsException: HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Moderator already exists for this community",
        ),
        ModeratorWorkerNotFoundException: HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderator worker not found",
        ),
        ModeratorWorkerAssignmentNotFoundException: HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Moderator worker assignment not found",
        ),
        ModeratorAlreadyAssignedException: HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Moderator is already assigned to a worker",
        ),
        NoAvailableModeratorWorkerException: HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No moderator worker has available capacity",
        ),
    }
