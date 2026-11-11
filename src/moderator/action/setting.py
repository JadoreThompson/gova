from pydantic import BaseModel


class ActionSettings(BaseModel):
    """
    Settings for actions in the moderator system.
    """

    requires_approval: bool
