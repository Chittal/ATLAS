from fastapi import Request, HTTPException, APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse
from schemas.user import UserSignup, UserLogin
from deps import templates
from helper.helper import get_current_user
from helper.pocketbase_helper import get_pb_admin_client

router = APIRouter(
    prefix="",
    tags=["Users"],
)


# Authentication routes
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "title": "Login"
    })

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    
    return templates.TemplateResponse("auth/signup.html", {
        "request": request,
        "title": "Sign Up"
    })

@router.post("/api/auth/signup")
async def signup(user_data: UserSignup):
    """User signup endpoint"""
    # try:  
    # Validate password confirmation
    if user_data.password != user_data.passwordConfirm:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Create user in PocketBase (let PocketBase handle password hashing)
    # For auth collections, we need to include passwordConfirm
    pb = get_pb_admin_client()
    user = pb.collection('users').create({
        "email": user_data.email,
        "password": user_data.password,
        "passwordConfirm": user_data.passwordConfirm,
        "name": user_data.name
    })
    
    return {
        "success": True,
        "message": "User created successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }
    # except Exception as e:
    #     raise HTTPException(status_code=400, detail=f"Signup failed: {str(e)}")

@router.post("/api/auth/login")
async def login(user_data: UserLogin, request: Request):
    """User login endpoint"""
    try:
        pb = get_pb_admin_client()
        # First check if user exists
        try:
            users = pb.collection('users').get_list(1, 1, {
                "filter": f"email = '{user_data.email}'"
            })
            if not users.items:
                raise HTTPException(status_code=401, detail="Invalid email or password")
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Use PocketBase's built-in authentication
        auth_data = pb.collection('users').auth_with_password(
            user_data.email,
            user_data.password
        )
        
        # Create response with cookie
        from fastapi.responses import JSONResponse
        response = JSONResponse({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": auth_data.record.id,
                "email": auth_data.record.email,
                "name": auth_data.record.name
            },
            "token": auth_data.token
        })
        
        # Set the auth token as an HTTP-only cookie
        response.set_cookie(
            key="auth_token",
            value=auth_data.token,
            max_age=7 * 24 * 60 * 60,  # 7 days
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        # Handle PocketBase authentication errors gracefully
        error_message = str(e)
        print(f"Login error: {error_message}")  # Debug logging
        
        # Check if it's a PocketBase authentication error
        if "Failed to authenticate" in error_message or "Status code:400" in error_message:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        elif "email" in error_message.lower():
            raise HTTPException(status_code=401, detail="Invalid email address")
        elif "password" in error_message.lower():
            raise HTTPException(status_code=401, detail="Invalid password")
        else:
            raise HTTPException(status_code=401, detail="Login failed. Please check your credentials and try again.")

@router.post("/api/auth/logout")
async def logout():
    """User logout endpoint"""
    try:
        pb = get_pb_admin_client()
        pb.auth_store.clear()
        
        # Create response and clear the cookie
        from fastapi.responses import JSONResponse
        response = JSONResponse({
            "success": True, 
            "message": "Logout successful"
        })
        
        # Clear the auth token cookie
        response.delete_cookie(
            key="auth_token",
            httponly=True,
            samesite="lax"
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@router.get("/api/auth/me")
async def get_current_user_info(request: Request):
    """Get current user information"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """Profile page"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # Gather user statistics
    try:
        from helper.pocketbase_helper import get_pb_admin_client
        admin_pb = get_pb_admin_client()
        
        # Get notes count
        notes = admin_pb.collection('notes').get_list(1, 500, {
            "filter": f"user_id = '{user.id}'"
        })
        notes_count = len(notes.items)
        
        # Get favorite notes count
        favorite_notes = [note for note in notes.items if getattr(note, 'is_favorite', False)]
        favorite_count = len(favorite_notes)
        
        # Get unique tags count
        all_tags = set()
        for note in notes.items:
            tags = getattr(note, 'tags', [])
            if isinstance(tags, list):
                all_tags.update(tags)
            elif isinstance(tags, str):
                try:
                    import json
                    parsed_tags = json.loads(tags)
                    if isinstance(parsed_tags, list):
                        all_tags.update(parsed_tags)
                except (json.JSONDecodeError, TypeError):
                    if tags.strip():
                        all_tags.add(tags.strip())
        tags_count = len(all_tags)
        
        # Get roadmaps count from user_roadmap_path table
        try:
            roadmaps = admin_pb.collection('user_roadmap_path').get_list(1, 500, {
                "filter": f"user_id = '{user.id}'"
            })
            roadmaps_count = len(roadmaps.items)
        except Exception as e:
            print(f"Error getting roadmaps count: {e}")
            roadmaps_count = 0
        
        # Prepare user data with statistics
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created": user.created,
            "updated": user.updated,
            "verified": getattr(user, 'verified', False),
            "statistics": {
                "notes_count": notes_count,
                "favorite_notes_count": favorite_count,
                "tags_count": tags_count,
                "roadmaps_count": roadmaps_count
            }
        }
        
    except Exception as e:
        print(f"Error gathering user statistics: {e}")
        # Fallback with basic user data
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created": user.created,
            "updated": user.updated,
            "verified": getattr(user, 'verified', False),
            "statistics": {
                "notes_count": 0,
                "favorite_notes_count": 0,
                "tags_count": 0,
                "roadmaps_count": 0
            }
        }
    
    return templates.TemplateResponse("profile_content.html", {
        "request": request,
        "title": "Profile",
        "user": user_data
    })
