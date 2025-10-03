import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    def __init__(self):
        self.api_base = os.getenv("API_BASE")
        self.api_key = os.getenv("API_KEY")
        self.model = os.getenv("MODEL", "llama3.1:8b")  # Default model
        self.llm_provider = os.getenv("CUSTOM_LLM_PROVIDER")


config = Config()
