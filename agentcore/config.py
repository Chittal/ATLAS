import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Logging setup: set LOG_LEVEL=DEBUG to see the debug output.
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    force=True,
)
for _noisy in ("httpx", "httpcore", "urllib3", "botocore", "boto3", "LiteLLM", "litellm", "langchain", "langsmith"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

class Config:
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION")
        self.model = os.getenv("MODEL")
        self.atlas_app_url = os.getenv("ATLAS_APP_URL")

app_config = Config()
