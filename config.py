import os
from dotenv import load_dotenv
from pocketbase import PocketBase

load_dotenv()

class Config:
    def __init__(self):
        self.api_base = os.getenv("API_BASE")
        self.api_key = os.getenv("API_KEY")
        self.model = os.getenv("MODEL", "llama3.1:8b")  # Default model
        self.llm_provider = os.getenv("CUSTOM_LLM_PROVIDER")
        
        # PocketBase configuration
        self.pocketbase_url = os.getenv("POCKETBASE_URL")
        self.pocketbase_email = os.getenv("POCKETBASE_EMAIL")
        self.pocketbase_password = os.getenv("POCKETBASE_PASSWORD")
        self.secret = os.getenv("SECRET")
        
        # # Initialize PocketBase connection
        # self.pb = None
        # if self.pocketbase_url and self.pocketbase_email and self.pocketbase_password:
        #     self.pb = PocketBase(self.pocketbase_url)
        #     try:
        #         self.pb.admins.auth_with_password(self.pocketbase_email, self.pocketbase_password)
        #         print("Connected to PocketBase with admin credentials")
        #     except Exception as e:
        #         print(f"Warning: Could not connect to PocketBase: {e}")
        #         self.pb = None


app_config = Config()
