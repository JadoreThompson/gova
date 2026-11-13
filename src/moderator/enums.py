from enum import Enum


class ModeratorStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
