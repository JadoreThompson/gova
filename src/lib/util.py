import uuid
from datetime import datetime, UTC


def get_datetime() -> datetime:
    """
    Returns the current datetime in UTC.
    """
    return datetime.now(tz=UTC)


def get_uuid() -> uuid.UUID:
    """
    Returns a new random UUID.
    """
    return uuid.uuid4()
