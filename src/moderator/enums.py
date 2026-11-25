from enum import Enum


class ModeratorPlatform(str, Enum):
    DISCORD = "discord"
    TWITCH = "twitch"
    YOUTUBE = "youtube"


class ModeratorStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNAVAILABLE = "unavailable"


class ModeratorWorkerStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNAVAILABLE = "unavailable"
