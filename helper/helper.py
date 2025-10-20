from deps import kuzu_manager
from fastapi import Request

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
            print(f"Token refresh failed: {refresh_error}")
            # If refresh fails, try to get user info directly
            try:
                # Try to get current user info without refresh
                user_info = client.collection('users').get_one(client.auth_store.model.id)
                if user_info:
                    return user_info
            except Exception as get_error:
                print(f"Get user info failed: {get_error}")
                return None
        
        return None
            
    except Exception as e:
        print(f"Auth validation error: {e}")
        return None
