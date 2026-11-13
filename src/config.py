import os
from dotenv import load_dotenv
from pathlib import Path

# Paths
# SRC_FOLDER = os.path.dirname(__file__)
SRC_FOLDER = Path(__file__).resolve().parent
# PROJECT_FOLDER = os.path.dirname(SRC_FOLDER)
PROJECT_FOLDER = SRC_FOLDER.parent

# load_dotenv(os.path.join(PROJECT_FOLDER, ".env"))
load_dotenv(PROJECT_FOLDER / ".env")


# Discord
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]


# LLM
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_MODEL_NAME = os.environ["LLM_MODEL_NAME"]
LLM_BASE_URL = os.environ["LLM_BASE_URL"]


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


# Postgres
POSTGRES_HOST = os.environ["POSTGRES_HOST"]
POSTGRES_PORT = int(os.environ["POSTGRES_PORT"])
POSTGRES_USERNAME = os.environ["POSTGRES_USERNAME"]
POSTGRES_PASSWORD = os.environ["POSTGRES_PASSWORD"]
POSTGRES_DB = os.environ["POSTGRES_DB"]

POSTGRES_HOST_CREDS = f"{POSTGRES_HOST}:{POSTGRES_PORT}"
POSTGRES_USER_CREDS = f"{POSTGRES_USERNAME}:{POSTGRES_PASSWORD}"


# Redis
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])
REDIS_USERNAME = os.environ["REDIS_USERNAME"]
REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
REDIS_DB = int(os.environ["REDIS_DB"])


# JWT
JWT_COOKIE_ALIAS = os.environ["JWT_COOKIE_ALIAS"]
JWT_ALGO = os.environ["JWT_ALGO"]
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_EXPIRY_SECS = int(os.environ["JWT_EXPIRY_SECS"])


IS_PRODUCTION = os.getenv("IS_PRODUCTION", "0") == "1"
