import logging
from deps import kuzu_manager
from fastapi import Request, HTTPException

def get_kuzu_manager():
    """Return shared Kuzu manager instance."""
    # Prefer the shared instance set during startup
    if kuzu_manager is not None:
        return kuzu_manager
    # Fallback to the app state if deps hasn't been populated yet
    try:
        from app import app as fastapi_app
        if hasattr(fastapi_app.state, "kuzu_manager") and fastapi_app.state.kuzu_manager is not None:
            return fastapi_app.state.kuzu_manager
    except Exception:
        pass
    raise RuntimeError("Kuzu manager not initialized")


def require_owned_roadmap_path(pb, user, user_roadmap_path_id: str):
    """Return the user_roadmap_path record if it belongs to `user`, else raise 404.

    Routes use the admin PocketBase client, which bypasses PocketBase's own access
    rules, so this check is what stops one user from reading or changing another
    user's roadmap path. A path owned by someone else gets the same 404 as a missing
    one, so the response doesn't reveal which IDs exist.
    """
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        record = pb.collection('user_roadmap_path').get_one(user_roadmap_path_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Roadmap path not found")
    if getattr(record, 'user_id', None) != user.id:
        logging.warning("User %s tried to access user_roadmap_path %s owned by another user", user.id, user_roadmap_path_id)
        raise HTTPException(status_code=404, detail="Roadmap path not found")
    return record


# Authentication helper functions
def get_current_user(request: Request):
    """Get current user from session using PocketBase auth validation"""
    # Get token from cookies
    token = request.cookies.get("auth_token")
    
    if not token:
        return None
    
    try:
        # Create a new PocketBase client instance to avoid corrupting the shared one
        from helper.pocketbase_helper import get_pb_client
        client = get_pb_client()
        
        # Set the token in the new client's auth store
        client.auth_store.save(token, {"id": "temp", "email": "temp"})
        
        # Try to refresh the token to validate it
        try:
            auth_data = client.collection('users').authRefresh()
            if auth_data and auth_data.record:
                return auth_data.record
        except Exception as refresh_error:
            logging.debug(f"Token refresh failed: {refresh_error}")
            # If refresh fails, try to get user info directly
            try:
                # Try to get current user info without refresh
                user_info = client.collection('users').get_one(client.auth_store.model.id)
                if user_info:
                    return user_info
            except Exception as get_error:
                logging.debug(f"Get user info failed: {get_error}")
                return None
        
        return None
            
    except Exception as e:
        logging.debug(f"Auth validation error: {e}")
        return None
