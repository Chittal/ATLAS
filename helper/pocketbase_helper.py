from config import app_config
from pocketbase import PocketBase
import httpx


def get_pb_admin_client():
    """Get a PocketBase admin client instance."""
    print("POCKETBASE URL:")
    print(app_config.pocketbase_url)
    print("POCKETBASE EMAIL:")
    print(app_config.pocketbase_email)
    print("POCKETBASE PASSWORD:")
    print(app_config.pocketbase_password)
    client = PocketBase(app_config.pocketbase_url, http_client=httpx.Client(verify=False))
    admin_data = client.admins.auth_with_password(app_config.pocketbase_email, app_config.pocketbase_password)
    if not admin_data.is_valid:
        raise Exception("Invalid PB credentials")
    return client

def get_pb_client() -> PocketBase:
    """Get a PocketBase client instance."""
    client = PocketBase(app_config.pocketbase_url, http_client=httpx.Client(verify=False))
    return client
