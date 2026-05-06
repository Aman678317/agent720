import os
from dotenv import load_dotenv

# Load .env safely
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()

def get_llm_provider():
    if not OPENAI_API_KEY:
        return "mock"
    return LLM_PROVIDER
