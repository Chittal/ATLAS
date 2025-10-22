import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION")
        self.model = os.getenv("MODEL")
        self.atlas_app_url = os.getenv("ATLAS_APP_URL")

app_config = Config()
