from fastapi.templating import Jinja2Templates
from helper.pocketbase_helper import get_pb_admin_client
from config import app_config

# Shared dependencies across the app
# pb = get_pb_admin_client()
templates = Jinja2Templates(directory="templates")

# Will be populated on startup from app.py
kuzu_manager = None

# URL helper functions for templates
def url_for_with_prefix(path: str) -> str:
    """Generate URL with prefix for templates"""
    if not path.startswith('/'):
        path = '/' + path
    if app_config.url_prefix:
        return app_config.url_prefix + path
    return path

def static_url(path: str) -> str:
    """Generate static URL with prefix for templates"""
    if not path.startswith('/'):
        path = '/' + path
    if app_config.url_prefix:
        return app_config.url_prefix + '/static' + path
    return '/static' + path

# Add helper functions to templates
templates.env.globals.update({
    'url_for_prefix': url_for_with_prefix,
    'static_url': static_url,
    'url_prefix': app_config.url_prefix
})


