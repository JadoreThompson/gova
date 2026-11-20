from enum import Enum


class ModeratorStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNAVAILABLE = "unavailable"


class ModeratorWorkerStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNAVAILABLE = "unavailable"
