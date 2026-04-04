import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "gpt-5.4-mini"
LINKTWIST_API_KEY = os.getenv("LINKTWIST_API_KEY")
LINKTWIST_BASE_URL = "https://sailingsantorini.api.link-twist.com"