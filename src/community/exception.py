from fastapi import HTTPException, status

from core.exception import ExceptionHandler


class CommunityNotFoundException(Exception):
    def __init__(self):
        super().__init__("Community not found")


class CommunityAlreadyExistsException(Exception):
    def __init__(self):
        super().__init__("Community already exists")


class CommunityHasActiveModeratorsException(Exception):
    def __init__(self):
        super().__init__("Community has moderators that are not offline")


class CommunityExceptionHandler(ExceptionHandler):
    exceptions = {
        CommunityNotFoundException: HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Community not found",
        ),
        CommunityAlreadyExistsException: HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Community already exists",
        ),
        CommunityHasActiveModeratorsException: HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Community has moderators that are not offline",
        ),
    }
