from fastapi import Request, HTTPException, APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse
from schemas.user import UserSignup, UserLogin
from deps import templates, pb
from helper.helper import get_current_user

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
async def login(user_data: UserLogin):
    """User login endpoint"""
    try:
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
        
        return {
            "success": True,
            "message": "Login successful",
            "user": {
                "id": auth_data.record.id,
                "email": auth_data.record.email,
                "name": auth_data.record.name
            },
            "token": auth_data.token
        }
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
        pb.auth_store.clear()
        return {"success": True, "message": "Logout successful"}
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
