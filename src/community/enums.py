from enum import Enum


class CommunityPlatform(str, Enum):
    DISCORD = "discord"
    TWITCH = "twitch"
    YOUTUBE = "youtube"
