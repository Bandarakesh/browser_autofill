import os
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
load_dotenv()

# Supports both naming conventions people commonly set in .env
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY")

def get_llm():
    # Plain LLM — use this for vision (multimodal) calls
    return ChatOpenAI(model="gpt-4o", api_key=api_key, temperature=0)

# Also export a module-level instance for convenience
model = init_chat_model(model="gpt-4o", api_key=api_key, temperature=0)