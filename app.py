from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Query, Body, Header, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from helper.kuzu_db_helper import KuzuSkillGraph
from agents.personalized_route_planning_agent import PersonalizedRoutePlanningAgent
from helper.pocketbase_helper import get_pb_admin_client
import deps
from config import app_config

from routes.users import router as users_router
from routes.roadmap_progress import router as roadmap_progress_router
from routes.learning_map import router as learning_map_router
from routes.notes import router as notes_router
from routes.agent import router as agent_router

import os
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="AI Learning Subway Map", description="Multi-user AI Learning Path Visualization")

# Initialize shared Kuzu manager and agent in startup events to avoid multi-process locks
@app.on_event("startup")
def on_startup():
    try:
        app.state.kuzu_manager = KuzuSkillGraph("skills_graph.db")
        deps.kuzu_manager = app.state.kuzu_manager
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
    allow_origins=["*"],  # Allows all origins (including AgentCore)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Specific methods
    allow_headers=["*"],  # Allows all headers (including X-API-Key)
)

# Mount static files with prefix
if app_config.url_prefix:
    static_prefix = f"{app_config.url_prefix}/static"
else:
    static_prefix = "/static"
app.mount(static_prefix, StaticFiles(directory="static"), name="static")

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "Learning Map API is running"}


# Include routers with prefix
prefix = app_config.url_prefix if app_config.url_prefix else ""
print(prefix, "prefix")
app.include_router(users_router, prefix=prefix)
app.include_router(roadmap_progress_router, prefix=prefix)
app.include_router(learning_map_router, prefix=prefix)
app.include_router(notes_router, prefix=prefix)
app.include_router(agent_router, prefix=prefix)

# Templates managed in deps.py

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8008))  # Use PORT env var or default to 8008
    uvicorn.run(app, host="0.0.0.0", port=port)
