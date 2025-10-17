from fastapi import FastAPI, Request, HTTPException, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from llm.groq import call_groq_model
from helper.kuzu_db_helper import KuzuSkillGraph
from agents.personalized_route_planning_agent import PersonalizedRoutePlanningAgent
from helper.user_progress_helper import UserProgressHelper
from helper.pocketbase_helper import get_pb_client, get_pb_admin_client

import os
from dotenv import load_dotenv
load_dotenv()

# Initialize PocketBase user client for auth flows
pb = get_pb_admin_client()

# Get secret key from environment for password hashing
SECRET_KEY = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY") or "your-secret-key-change-this-in-production"

# Authentication models
class UserSignup(BaseModel):
    email: str
    password: str
    passwordConfirm: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

# Security
security = HTTPBearer()

# Note: Using PocketBase's built-in password hashing and authentication

app = FastAPI(title="AI Learning Subway Map", description="Multi-user AI Learning Path Visualization")

# Initialize shared Kuzu manager and agent in startup events to avoid multi-process locks
@app.on_event("startup")
def on_startup():
    try:
        app.state.kuzu_manager = KuzuSkillGraph("skills_graph.db")
        app.state.agent = PersonalizedRoutePlanningAgent(kuzu_helper=app.state.kuzu_manager)
        print("✅ LangGraph agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize LangGraph agent: {e}")
        app.state.agent = None

@app.on_event("shutdown")
def on_shutdown():
    try:
        if hasattr(app.state, "kuzu_manager") and app.state.kuzu_manager:
            app.state.kuzu_manager.close()
    except Exception:
        pass

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")


@app.get("/roadmap/progression", response_class=HTMLResponse)
async def roadmap_progression_page(request: Request):
    """Roadmap progression visualization page"""
    return templates.TemplateResponse("roadmap_progression.html", {
        "request": request,
        "title": "Roadmap"
    })

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Home page"""
    user = get_current_user(request)
    print(f"Main page access - User: {user}")  # Debug logging
    
    # Redirect to login if no authenticated user
    if not user:
        print("No user found, redirecting to login")  # Debug logging
        return RedirectResponse(url="/login", status_code=302)
    
    print(f"User authenticated: {user.email}")  # Debug logging
    return templates.TemplateResponse("skills_graph_flat.html", {
        "request": request,
        "title": "Roadmap Kuzu Graph Style",
        "user": user
    })

@app.get("/home-content", response_class=HTMLResponse)
async def home_content(request: Request):
    """Home page content for HTMX navigation"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("skills_graph_content.html", {
        "request": request,
        "user": user
    })

@app.get("/notes", response_class=HTMLResponse)
async def notes_page(request: Request):
    """Notes page"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("notes.html", {
        "request": request,
        "user": user
    })

@app.get("/notes-content", response_class=HTMLResponse)
async def notes_content(request: Request):
    """Notes page content for HTMX navigation"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("notes_content.html", {
        "request": request,
        "user": user
    })

@app.get("/roadmaps", response_class=HTMLResponse)
async def roadmaps_page(request: Request):
    """Roadmaps page"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("roadmaps.html", {
        "request": request,
        "user": user
    })

@app.get("/roadmaps-content", response_class=HTMLResponse)
async def roadmaps_content(request: Request):
    """Roadmaps page content for HTMX navigation"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("roadmaps_content.html", {
        "request": request,
        "user": user
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": user
    })

@app.get("/settings-content", response_class=HTMLResponse)
async def settings_content(request: Request):
    """Settings page content for HTMX navigation"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("settings_content.html", {
        "request": request,
        "user": user
    })

@app.get("/skills", response_class=HTMLResponse)
async def skills_page(request: Request):
    """Skills page"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("skills.html", {
        "request": request,
        "user": user
    })

@app.get("/skills-content", response_class=HTMLResponse)
async def skills_content(request: Request):
    """Skills page content for HTMX navigation"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("skills_content.html", {
        "request": request,
        "user": user
    })

@app.get("/learning-path", response_class=HTMLResponse)
async def learning_path_page(request: Request, start: str = "data analyst", end: str = "ai agents"):
    """Focused learning path visualization page showing only the highlighted path"""
    user = get_current_user(request)
    
    # Redirect to login if no authenticated user
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("learning_path.html", {
        "request": request,
        "start_skill": start,
        "end_skill": end,
        "title": f"Learning Path: {start} → {end}",
        "user": user
    })

def get_kuzu_manager():
    """Return shared Kuzu manager instance."""
    if not hasattr(app.state, "kuzu_manager") or app.state.kuzu_manager is None:
        raise RuntimeError("Kuzu manager not initialized")
    return app.state.kuzu_manager


@app.get("/api/roadmap-progression")
async def get_roadmap_progression():
    """Get skills organized in roadmap progression levels"""
    try:
        manager = get_kuzu_manager()
        progression = manager.get_roadmap_progression()
        
        # Convert to Cytoscape.js format with level-based positioning
        nodes = []
        edges = []
        
        level_x_spacing = 400
        level_y_spacing = 150
        
        # Get level names from the levels dictionary
        level_names = list(progression["levels"].keys())
        
        for level_idx, level_name in enumerate(level_names):
            level_skills = progression["levels"].get(level_name, [])
            level_x = level_idx * level_x_spacing + 200
            
            for skill_idx, skill in enumerate(level_skills):
                # Position skills vertically within each level
                skill_y = skill_idx * level_y_spacing + 200
                
                nodes.append({
                    "data": {
                        "id": skill["id"],
                        "name": skill["name"],
                        "description": skill.get("description", ""),
                        "level": level_name,
                        "level_index": level_idx,
                        "skill_index": skill_idx
                    },
                    "position": {
                        "x": level_x,
                        "y": skill_y
                    },
                    "classes": f"level-{level_idx} {level_name.replace('_', '-')}"
                })
        
        # Add only the real skill connections from the database
        for connection in progression["connections"]:
            from_skill_id = connection["from_skill"]
            to_skill_id = connection["to_skill"]
            
            # Only add the connection if both skills exist in our nodes
            from_exists = any(node["data"]["id"] == from_skill_id for node in nodes)
            to_exists = any(node["data"]["id"] == to_skill_id for node in nodes)
            
            if from_exists and to_exists:
                edges.append({
                    "data": {
                        "id": f"{from_skill_id}-{to_skill_id}",
                        "source": from_skill_id,
                        "target": to_skill_id,
                        "relationship_type": connection.get("relationship_type", "prerequisite"),
                        "weight": connection.get("weight", 1)
                    },
                    "classes": "progression-edge"
                })
        
        return {
            "format_version": "1.0",
            "generated_by": "learning-map-app",
            "elements": {
                "nodes": nodes,
                "edges": edges
            },
            "levels": progression["levels"],
            "level_names": level_names,
            "total_skills": progression["total_skills"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting roadmap progression: {str(e)}")

@app.get("/api/roadmap-flat")
async def get_roadmap_flat():
    """Get a flat skills graph (no levels) for comparison with progression layout."""
    try:
        manager = get_kuzu_manager()
        skills = manager.get_all_skills()
        connections = manager.get_all_skill_connections()

        nodes = []
        edges = []

        # Build nodes without level grouping or explicit positions
        for skill in skills:
            nodes.append({
                "data": {
                    "id": skill["id"],
                    "name": skill["name"],
                    "description": skill.get("description", ""),
                    "order_index": skill.get("order_index", 0)
                }
            })

        # Build edges directly from skill connections
        for connection in connections:
            edges.append({
                "data": {
                    "id": f"{connection['from_skill']}-{connection['to_skill']}",
                    "source": connection["from_skill"],
                    "target": connection["to_skill"],
                    "relationship_type": connection.get("relationship_type", "prerequisite"),
                    "weight": connection.get("weight", 1)
                }
            })

        return {
            "format_version": "1.0",
            "generated_by": "learning-map-app",
            "elements": {
                "nodes": nodes,
                "edges": edges
            },
            "total_skills": len(skills),
            "total_edges": len(edges)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting flat roadmap: {str(e)}")

@app.get("/api/skill-path")
async def get_skill_path(start: str, end: str):
    """Get a learning path between two skills (by name) using KuzuDB graph.

    Returns a list of skill ids representing the path, and also the corresponding
    edges between consecutive skills for easy highlighting on the client.
    """
    # try:
    manager = get_kuzu_manager()
    print(start, end, "start, end")
    paths = manager.find_learning_path(start, end)
    print(paths, "paths")
    if not paths:
        return {"path": [], "edges": []}

    edges = []
    for i in range(len(paths) - 1):
        source = paths[i]["id"]
        target = paths[i + 1]["id"]
        edges.append({
            "id": f"{source}-{target}",
            "source": source,
            "target": target
        })

    return {
        "path": paths,
        "edges": edges
    }
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error finding skill path: {str(e)}")

@app.get("/api/learning-path-info")
async def get_learning_path_info(start: str, end: str):
    """Get detailed learning path information for HTMX partial updates."""
    try:
        manager = get_kuzu_manager()
        paths = manager.find_learning_path(start, end)
        
        if not paths:
            raise HTTPException(status_code=404, detail="No learning path found between these skills")
        
        total_skills = len(paths)
        estimated_time = f"{int(total_skills * 2)} weeks"
        difficulty = "Beginner" if total_skills <= 3 else "Intermediate" if total_skills <= 6 else "Advanced"
        
        skill_names = [skill["name"] for skill in paths]
        description = f"This learning path will take you through {total_skills} essential skills, from {skill_names[0]} to {skill_names[-1]}. Each skill builds upon the previous one, creating a solid foundation for your learning journey."
        
        return {
            "total_skills": total_skills,
            "estimated_time": estimated_time,
            "difficulty": difficulty,
            "description": description,
            "skills": paths,
            "start_skill": start,
            "end_skill": end
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting learning path info: {str(e)}")

@app.get("/api/learning-path-info-partial", response_class=HTMLResponse)
async def get_learning_path_info_partial(request: Request, start: str, end: str):
    """Get learning path information as HTML partial for HTMX."""
    try:
        manager = get_kuzu_manager()
        paths = manager.find_learning_path(start, end)
        
        if not paths:
            return templates.TemplateResponse("partials_learning_path_info.html", {
                "request": request,
                "total_skills": 0,
                "estimated_time": "N/A",
                "difficulty": "Unknown",
                "description": "No learning path found between these skills.",
                "skills": []
            })
        
        total_skills = len(paths)
        estimated_time = f"{int(total_skills * 2)} weeks"
        difficulty = "Beginner" if total_skills <= 3 else "Intermediate" if total_skills <= 6 else "Advanced"
        
        skill_names = [skill["name"] for skill in paths]
        description = f"This learning path will take you through {total_skills} essential skills, from {skill_names[0]} to {skill_names[-1]}. Each skill builds upon the previous one, creating a solid foundation for your learning journey."
        
        return templates.TemplateResponse("partials_learning_path_info.html", {
            "request": request,
            "total_skills": total_skills,
            "estimated_time": estimated_time,
            "difficulty": difficulty,
            "description": description,
            "skills": paths
        })
    except Exception as e:
        return templates.TemplateResponse("partials_learning_path_info.html", {
            "request": request,
            "total_skills": 0,
            "estimated_time": "Error",
            "difficulty": "Unknown",
            "description": f"Error loading path: {str(e)}",
            "skills": []
        })

@app.get("/api/skill/{skill_id}")
async def get_skill_details(skill_id: str):
    """Get detailed information about a specific skill."""
    try:
        manager = get_kuzu_manager()
        skill = manager.get_skill_by_id(skill_id)
        
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        
        # Get related skills (prerequisites and next skills)
        prerequisites = manager.get_skill_prerequisites(skill_id)
        next_skills = manager.get_skill_next_skills(skill_id)
        
        return {
            "id": skill["id"],
            "name": skill["name"],
            "description": skill.get("description", ""),
            "level": skill.get("level", ""),
            "order_index": skill.get("order_index", 0),
            "prerequisites": prerequisites,
            "next_skills": next_skills,
            "total_prerequisites": len(prerequisites),
            "total_next_skills": len(next_skills)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting skill details: {str(e)}")

@app.get("/api/skill/{skill_name}/learning-nodes")
async def get_learning_nodes_by_skill(skill_name: str):
    """Get learning nodes for a specific skill by name."""
    try:
        manager = get_kuzu_manager()
        learning_nodes = manager.get_learning_nodes_by_skill_name(skill_name)
        
        return {
            "skill_name": skill_name,
            "learning_nodes": learning_nodes,
            "total_nodes": len(learning_nodes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting learning nodes: {str(e)}")

@app.get("/api/skill/{skill_name}/learning-graph")
async def get_learning_graph_by_skill(skill_name: str, user_roadmap_path_id: str | None = None, skill_id: str | None = None):
    """Get learning nodes and edges for a specific skill by name to create a connected graph."""
    try:
        manager = get_kuzu_manager()
        learning_nodes = manager.get_learning_nodes_by_skill_name(skill_name)
        skill_edges = manager.get_skill_edges(skill_name)
        
        # Update learning_nodes_count in roadmap_path_skills table
        try:
            progress_helper = UserProgressHelper(get_pb_admin_client())
            # Resolve roadmap_path_id from user_roadmap_path_id if needed
            if user_roadmap_path_id:
                try:
                    mapping_rec = progress_helper.pb.collection('user_roadmap_path').get_one(user_roadmap_path_id)
                    roadmap_path_id = getattr(mapping_rec, 'roadmap_path_id', None)
                    print(f"Resolved roadmap_path_id from user_roadmap_path_id {user_roadmap_path_id}: {roadmap_path_id}")
                except Exception as resolve_err:
                    print(f"Warning: could not resolve roadmap_path_id from user_roadmap_path_id {user_roadmap_path_id}: {resolve_err}")

            if roadmap_path_id and skill_id:
                print(f"Updating learning nodes count by ids: {roadmap_path_id}, {skill_id}")
                progress_helper.update_learning_nodes_count_by_ids(roadmap_path_id, skill_id, len(learning_nodes))
            else:
                print(f"Updating learning nodes count by name: {skill_name}")
                progress_helper.update_learning_nodes_count(skill_name, len(learning_nodes))
            print(f"Learning nodes count updated for {skill_name}")
            print(f"Learning nodes count: {len(learning_nodes)}")
        except Exception as update_error:
            # Don't fail the main request if the count update fails
            print(f"Warning: Could not update learning nodes count for {skill_name}: {update_error}")
        
        return {
            "skill_name": skill_name,
            "learning_nodes": learning_nodes,
            "edges": skill_edges,
            "total_nodes": len(learning_nodes),
            "total_edges": len(skill_edges)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting learning graph: {str(e)}")

@app.get("/api/learning-node/{learning_node_id}/resources")
async def get_learning_node_resources(learning_node_id: str):
    """Get resources for a specific learning node by ID."""
    try:
        manager = get_kuzu_manager()
        resources = manager.get_resources_by_learning_node_id(learning_node_id)
        
        return {
            "learning_node_id": learning_node_id,
            "resources": resources,
            "total_resources": len(resources)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting learning node resources: {str(e)}")

@app.post("/api/skill/{skill_id}/chat")
async def chat_about_skill(skill_id: str, message: dict):
    """Chat about a specific skill - placeholder for AI chat functionality."""
    try:
        # For now, return a simple response
        # In a real implementation, this would integrate with an AI service
        user_message = message.get("message", "")
        
        # Simple response based on skill context

        # response = f"I can help you learn about {skill_id}. You asked: '{user_message}'. This is a placeholder response that would normally be generated by an AI assistant."
        response = call_groq_model(
            messages=[
                {"role": "user", "content": user_message}
            ],
            system_prompt="You are a helpful assistant that can answer questions about the skill.",
            model="llama-3.1-8b-instant"
        )
        return {
            "skill_id": skill_id,
            "user_message": user_message,
            "ai_response": response,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

@app.post("/api/skill/query")
async def query_skills(message: dict):
    """Handle general skill queries from the chat widget."""
    try:
        user_message = message.get("message", "")
        
        # Get all skills for context
        manager = get_kuzu_manager()
        all_skills = manager.get_all_skills()
        skill_names = [skill["name"] for skill in all_skills]
        
        system_prompt = f"""You are a helpful learning assistant for a skills roadmap. 
        Available skills include: {', '.join(skill_names[:20])} and many more.
        You can help users understand learning paths, prerequisites, and skill relationships.
        Be concise and helpful. If asked about paths, suggest using the format 'Find path from X to Y'."""
        
        response = call_groq_model(
            messages=[
                {"role": "user", "content": user_message}
            ],
            system_prompt=system_prompt,
            model="llama-3.1-8b-instant"
        )
        
        return {
            "response": response,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing skill query: {str(e)}")

@app.post("/api/general/chat")
async def general_chat(request: Request):
    """Handle general chat queries from the chat widget."""
    print("ENDPOINT HIT! /api/skill/general/chat was called!")
    # try:
    request_json = await request.json()
    user_message = request_json.get("message", "")
    print(f"API called with message: '{user_message}'")
    print(f"Full message dict: {request_json}")
    # Use the global LangGraph agent
    print("CALLING LANGGRAPH AGENT")
    result = app.state.agent.execute_graph(user_message)
    print("Agent result:", result)
    
    # Extract the response from the agent result
    if result.get("status") == "success" and result.get("messages"):
        assistant_messages = [msg for msg in result["messages"] if msg["role"] == "assistant"]
        if assistant_messages:
            ai_response = assistant_messages[-1]["content"]
        else:
            ai_response = "I'm sorry, I couldn't process your request."
    else:
        ai_response = f"I encountered an issue: {result.get('error', 'Unknown error')}"
    
    response_data = {
        "ai_response": ai_response,
        "timestamp": "2024-01-01T00:00:00Z",
        "agent_metadata": {
            "category": result.get("category"),
            "step": result.get("step"),
            "status": result.get("status")
        }
    }
    
    # If this is a route planning query, get the path data for highlighting
    if result.get("category") == "ROUTE_PLANNING" and result.get("path_objects"):
        try:
            path_objects = result.get("path_objects")
            print(f"Route planning path objects: {path_objects}")
            
            # Create edges for the path
            edges = []
            for i in range(len(path_objects) - 1):
                source = path_objects[i]["id"]
                target = path_objects[i + 1]["id"]
                edges.append({
                    "id": f"{source}-{target}",
                    "source": source,
                    "target": target
                })
            
            path_data = {
                "path": path_objects,
                "edges": edges
            }
            print(f"Path data for highlighting: {path_data}")
            response_data["path_data"] = path_data
        except Exception as e:
            print(f"Error creating path data: {e}")
    
    return response_data
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

# Authentication helper functions
def get_current_user(request: Request):
    """Get current user from session"""
    # Try to get token from cookies first
    token = request.cookies.get("auth_token")
    
    # Also check Authorization header as fallback
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
    
    print(f"Auth token from cookie/header: {token[:20] if token else 'None'}...")  # Debug logging
    
    if not token:
        return None
    
    try:
        # Use PocketBase's auth refresh to validate token
        print(f"Attempting to validate token with PocketBase authRefresh...")  # Debug logging
        
        # Set the token in auth store first
        pb.auth_store.save(token, {"id": "temp", "email": "temp"})
        
        # Try to refresh the auth (this validates the token)
        auth_data = pb.collection('users').authRefresh()
        
        if auth_data and auth_data.record:
            user = auth_data.record
            print(f"User found via authRefresh: {user.email}")  # Debug logging
            return user
        else:
            print("Auth refresh failed - no user returned")  # Debug logging
            return None
            
    except Exception as e:
        print(f"Auth refresh validation error: {e}")  # Debug logging
        print(f"Error type: {type(e)}")  # Debug logging
        
        # Fallback: Try to decode JWT token manually
        try:
            import base64
            import json
            
            # JWT tokens have 3 parts separated by dots
            token_parts = token.split('.')
            if len(token_parts) == 3:
                # Decode the payload (second part)
                payload = token_parts[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.b64decode(payload)
                token_data = json.loads(decoded)
                print(f"Token payload: {token_data}")
                
                # Try to get user by ID from token
                if 'id' in token_data:
                    user = pb.collection('users').get_one(token_data['id'])
                    print(f"Found user by ID: {user.email}")
                    return user
        except Exception as decode_e:
            print(f"Manual token decode failed: {decode_e}")
        
        return None

# Authentication routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/home-content", status_code=302)
    
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "title": "Login"
    })

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Signup page"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/home-content", status_code=302)
    
    return templates.TemplateResponse("auth/signup.html", {
        "request": request,
        "title": "Sign Up"
    })

@app.post("/api/auth/signup")
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

@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    """User login endpoint"""
    # try:
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
    # except HTTPException:
    #     raise
    # except Exception as e:
    #     # Handle PocketBase authentication errors gracefully
    #     error_message = str(e)
    #     print(f"Login error: {error_message}")  # Debug logging
        
    #     # Check if it's a PocketBase authentication error
    #     if "Failed to authenticate" in error_message or "Status code:400" in error_message:
    #         raise HTTPException(status_code=401, detail="Invalid email or password")
    #     elif "email" in error_message.lower():
    #         raise HTTPException(status_code=401, detail="Invalid email address")
    #     elif "password" in error_message.lower():
    #         raise HTTPException(status_code=401, detail="Invalid password")
    #     else:
    #         raise HTTPException(status_code=401, detail="Login failed. Please check your credentials and try again.")

@app.post("/api/auth/logout")
async def logout():
    """User logout endpoint"""
    try:
        pb.auth_store.clear()
        return {"success": True, "message": "Logout successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@app.get("/api/auth/me")
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

@app.post("/api/route-planning/start-learning")
async def start_learning_track(request: Request, track_data: dict):
    """Save user's learning track when they click 'Start Learning'"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Extract track information from the request
        start_skill = track_data.get("start_skill")
        target_skill = track_data.get("target_skill")
        skill_path = track_data.get("skill_path", [])
        
        if not start_skill or not target_skill or not skill_path:
            raise HTTPException(status_code=400, detail="Missing required track data")
        
        # Initialize user progress helper with an admin client for DB writes
        admin_pb = get_pb_admin_client()
        progress_helper = UserProgressHelper(admin_pb)
        
        # Save the user's roadmap path
        result = progress_helper.save_user_roadmap_path(
            user_id=user.id,
            start_skill=start_skill,
            target_skill=target_skill,
            skill_path=skill_path
        )
        
        return {
            "success": True,
            "message": "Learning track saved successfully",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save learning track: {str(e)}")

@app.get("/api/user/progress")
async def get_user_progress(request: Request):
    """Get user's learning progress"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Use admin client for reading user progress
        progress_helper = UserProgressHelper(get_pb_admin_client())
        user_paths = progress_helper.get_user_roadmap_paths(user.id)
        
        return {
            "success": True,
            "user_paths": user_paths
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user progress: {str(e)}")

@app.post("/api/user/progress/update")
async def update_user_progress(request: Request, progress_data: dict):
    """Update user's progress on a learning path"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        user_roadmap_path_id = progress_data.get("user_roadmap_path_id")
        progress = progress_data.get("progress", 0.0)
        completed_at = progress_data.get("completed_at")
        
        if not user_roadmap_path_id:
            raise HTTPException(status_code=400, detail="Missing user_roadmap_path_id")
        
        progress_helper = UserProgressHelper(get_pb_admin_client())
        result = progress_helper.update_user_progress(
            user_roadmap_path_id=user_roadmap_path_id,
            progress=progress,
            completed_at=completed_at
        )
        
        return {
            "success": True,
            "message": "Progress updated successfully",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")

@app.post("/api/learning-node/complete")
async def complete_learning_node(request: Request, completion_data: dict):
    """Mark a learning node as completed"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        learning_node_id = completion_data.get("learning_node_id")
        skill_id = completion_data.get("skill_id")
        user_roadmap_path_id = completion_data.get("user_roadmap_path_id")
        completed_at = completion_data.get("completed_at")
        
        if not learning_node_id or not skill_id or not user_roadmap_path_id:
            raise HTTPException(status_code=400, detail="Missing required fields: learning_node_id, skill_id, user_roadmap_path_id")
        
        progress_helper = UserProgressHelper(get_pb_admin_client())
        result = progress_helper.save_learning_node_completion(
            user_id=user.id,
            learning_node_id=learning_node_id,
            skill_id=skill_id,
            user_roadmap_path_id=user_roadmap_path_id,
            completed_at=completed_at
        )
        
        return {
            "success": True,
            "message": f"Learning node {result['action']} successfully",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete learning node: {str(e)}")

@app.post("/api/learning-node/incomplete")
async def incomplete_learning_node(request: Request, completion_data: dict):
    """Mark a learning node as incomplete (remove completion)"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        learning_node_id = completion_data.get("learning_node_id")
        user_roadmap_path_id = completion_data.get("user_roadmap_path_id")
        
        if not learning_node_id or not user_roadmap_path_id:
            raise HTTPException(status_code=400, detail="Missing required fields: learning_node_id, user_roadmap_path_id")
        
        progress_helper = UserProgressHelper(get_pb_admin_client())
        result = progress_helper.remove_learning_node_completion(
            user_id=user.id,
            learning_node_id=learning_node_id,
            user_roadmap_path_id=user_roadmap_path_id
        )
        
        return {
            "success": True,
            "message": f"Learning node {result['action']} successfully",
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark learning node incomplete: {str(e)}")

@app.get("/api/learning-node/progress")
async def get_learning_node_progress(request: Request, user_roadmap_path_id: str = None):
    """Get user's learning node progress"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        progress_helper = UserProgressHelper(get_pb_admin_client())
        progress_records = progress_helper.get_user_learning_node_progress(
            user_id=user.id,
            user_roadmap_path_id=user_roadmap_path_id
        )
        
        return {
            "success": True,
            "progress_records": progress_records,
            "total_completed": len(progress_records)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get learning node progress: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
