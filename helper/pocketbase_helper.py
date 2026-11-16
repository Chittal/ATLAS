import logging
from config import app_config
from pocketbase import PocketBase
import httpx


def get_pb_admin_client():
    """Get a PocketBase admin client instance."""
    logging.debug("POCKETBASE URL:")
    logging.debug(app_config.pocketbase_url)
    logging.debug("POCKETBASE EMAIL:")
    logging.debug(app_config.pocketbase_email)
    logging.debug("POCKETBASE PASSWORD:")
    logging.debug(app_config.pocketbase_password)
    client = PocketBase(app_config.pocketbase_url, http_client=httpx.Client(verify=False))
    admin_data = client.admins.auth_with_password(app_config.pocketbase_email, app_config.pocketbase_password)
    if not admin_data.is_valid:
        raise Exception("Invalid PB credentials")
    return client

def pb_escape(value) -> str:
    """Escape a value for use inside a single-quoted PocketBase filter string.

    The Python SDK has no parameter binding, so any user-supplied value placed
    in a filter must go through this; otherwise a `'` in the value can end the
    string and add conditions (e.g. reading other users' records).
    """
    return str(value).replace("\\", "\\\\").replace("'", "\\'")


def get_pb_client() -> PocketBase:
    """Get a PocketBase client instance."""
    client = PocketBase(app_config.pocketbase_url, http_client=httpx.Client(verify=False))
    return client
