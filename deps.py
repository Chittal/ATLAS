from fastapi.templating import Jinja2Templates
from helper.pocketbase_helper import get_pb_admin_client

# Shared dependencies across the app
# pb = get_pb_admin_client()
templates = Jinja2Templates(directory="templates")

# Will be populated on startup from app.py
kuzu_manager = None


