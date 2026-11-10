from datetime import datetime, UTC


def get_datetime() -> datetime:
    """
    Returns the current datetime in UTC.
    """
    return datetime.now(tz=UTC)
