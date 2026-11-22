import logging
import os
import sys
from dotenv import load_dotenv
from pathlib import Path

# Paths
SRC_FOLDER = Path(__file__).resolve().parent
PROJECT_FOLDER = SRC_FOLDER.parent

load_dotenv(PROJECT_FOLDER / ".env")


# Postgres
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = int(os.environ["POSTGRES_PORT"])
POSTGRES_USERNAME = os.environ["POSTGRES_USERNAME"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]

POSTGRES_HOST_CREDS = f"{POSTGRES_HOST}:{POSTGRES_PORT}"
POSTGRES_USER_CREDS = f"{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}"


# Kafka
KAFKA_BOOTSTRAP_SERVERS = os.environ["KAFKA_BOOTSTRAP_SERVERS"]
KAFKA_MODERATOR_ACTIONS_TOPIC = os.environ.get(
    "KAFKA_MODERATOR_ACTIONS_TOPIC", "moderator_actions"
)
KAFKA_MODERATOR_EVENTS_TOPIC = os.environ.get(
    "KAFKA_MODERATOR_EVENTS_TOPIC", "moderator_events"
)
KAFKA_MODERATOR_EVENTS_GROUP_ID = os.environ.get(
    "KAFKA_MODERATOR_EVENTS_GROUP_ID", "moderator-manager"
)


# Redis
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])
REDIS_USERNAME = os.environ["REDIS_USERNAME"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
REDIS_DB = int(os.environ["REDIS_DB"])


# LLM
LLM_BASE_URL = os.environ["LLM_BASE_URL"]
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_MODEL_NAME = os.environ["LLM_MODEL_NAME"]


# Discord
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]


# Twitch
# Client credentials are used to generate/refresh the app token and to manage
# the bot's user token. The bot token/refresh token are optional so that a
# previously saved TwitchIO token file can be reused instead.
TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET", "")
TWITCH_BOT_ID = os.environ.get("TWITCH_BOT_ID", "")
TWITCH_BOT_TOKEN = os.environ.get("TWITCH_BOT_TOKEN", "")
TWITCH_BOT_REFRESH_TOKEN = os.environ.get("TWITCH_BOT_REFRESH_TOKEN", "")


# HTTP API
APP_ALLOWED_ORIGINS = os.environ["APP_ALLOWED_ORIGINS"].split(",")
APP_ALLOWED_HEADERS = os.environ["APP_ALLOWED_HEADERS"].split(",")
APP_ALLOWED_METHODS = os.environ["APP_ALLOWED_METHODS"].split(",")
APP_ALLOW_CREDENTIALS = os.environ["APP_ALLOW_CREDENTIALS"] == "1"


# JWT Configuration
JWT_COOKIE_ALIAS = os.environ["JWT_COOKIE_ALIAS"]
JWT_ALGO = os.environ["JWT_ALGO"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_EXPIRY_SECS = int(os.environ["JWT_EXPIRY_SECS"])


# Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

aiokafka_logger = logging.getLogger("aiokafka")
aiokafka_logger.setLevel(logging.WARNING)

kafka_logger = logging.getLogger("kafka")
kafka_logger.setLevel(logging.WARNING)

del logger
del handler


# Environment
IS_PRODUCTION = os.getenv("IS_PRODUCTION", "0") == "1"
