import os
from dotenv import load_dotenv

# Paths
SRC_FOLDER = os.path.dirname(__file__)
PROJECT_FOLDER = os.path.dirname(SRC_FOLDER)

load_dotenv(os.path.join(PROJECT_FOLDER, ".env"))


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
