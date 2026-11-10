import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))


# Discord
DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]


# LLM
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gpt-5.2")
LLM_BASE_URL = os.environ["LLM_BASE_URL"]
