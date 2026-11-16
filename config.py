import logging
import os
from dotenv import load_dotenv
from pocketbase import PocketBase

load_dotenv()

# Logging setup: set LOG_LEVEL=DEBUG in .env to see the debug output.
# force=True replaces any handler a library installed before this import.
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)
# Keep noisy third-party libraries quiet even when LOG_LEVEL=DEBUG
for _noisy in ("httpx", "httpcore", "urllib3", "botocore", "boto3", "LiteLLM", "litellm", "openai", "langchain", "langsmith"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

class Config:
    def __init__(self):
        self.api_base = os.getenv("API_BASE") or os.getenv("LITELLM_API_BASE")
        self.api_key = os.getenv("API_KEY") or os.getenv("LITELLM_API_KEY")
        self.llm_provider = os.getenv("CUSTOM_LLM_PROVIDER") or os.getenv("LITELLM_LLM_PROVIDER")
        self.aws_region = os.getenv("AWS_REGION")
        self.aws_account_id = os.getenv("AWS_ACCOUNT_ID")
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.model = os.getenv("MODEL")
        logging.debug("%s %s", self.model, "self.model")
        self.agent_runtime_arn = os.getenv("AGENT_RUNTIME_ARN")
        
        # PocketBase configuration
        self.pocketbase_url = os.getenv("POCKETBASE_URL")
        self.pocketbase_email = os.getenv("POCKETBASE_EMAIL")
        self.pocketbase_password = os.getenv("POCKETBASE_PASSWORD")
        self.secret = os.getenv("SECRET")
        
        # URL prefix configuration
        url_prefix = os.getenv("URL_PREFIX", "").rstrip("/")
        if url_prefix and not url_prefix.startswith("/"):
            url_prefix = "/" + url_prefix
        self.url_prefix = url_prefix
        logging.debug("%s %s", self.url_prefix, "self.url_prefix")
        
        # # Initialize PocketBase connection
        # self.pb = None
        # if self.pocketbase_url and self.pocketbase_email and self.pocketbase_password:
        #     self.pb = PocketBase(self.pocketbase_url)
        #     try:
        #         self.pb.admins.auth_with_password(self.pocketbase_email, self.pocketbase_password)
        #         logging.debug("Connected to PocketBase with admin credentials")
        #     except Exception as e:
        #         logging.debug(f"Warning: Could not connect to PocketBase: {e}")
        #         self.pb = None


app_config = Config()
