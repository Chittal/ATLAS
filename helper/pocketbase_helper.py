import os
from pocketbase import PocketBase

from dotenv import load_dotenv
load_dotenv()

pb = PocketBase(os.getenv("POCKETBASE_URL"))
pb.admins.auth_with_password(os.getenv("POCKETBASE_EMAIL"), os.getenv("POCKETBASE_PASSWORD"))
