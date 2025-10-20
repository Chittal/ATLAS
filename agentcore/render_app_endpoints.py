"""
API endpoints that need to be added to the main Render app
to support the AgentCore agent communication.

Add these endpoints to your main app.py or create a new router.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import deps

# Create router for agent endpoints
agent_router = APIRouter(prefix="/api/agent", tags=["agent"])

# Pydantic models for request/response
class LearningPathRequest(BaseModel):
    start_skill: str
    target_skill: str

class LearningPathResponse(BaseModel):
    path: List[Dict[str, Any]]
    status: str

class SkillsResponse(BaseModel):
    skills: List[Dict[str, Any]]
    status: str

class ConnectionsResponse(BaseModel):
    connections: List[Dict[str, Any]]
    status: str

class PrerequisitesResponse(BaseModel):
    prerequisites: List[Dict[str, Any]]
    status: str

class SkillDetailsResponse(BaseModel):
    skill: Optional[Dict[str, Any]]
    status: str

@agent_router.get("/skills", response_model=SkillsResponse)
async def get_all_skills():
    """Get all available skills from the database"""
    try:
        if not hasattr(deps, 'kuzu_manager') or deps.kuzu_manager is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        skills = deps.kuzu_manager.get_all_skills()
        return SkillsResponse(skills=skills, status="success")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving skills: {str(e)}")

@agent_router.get("/skill-connections", response_model=ConnectionsResponse)
async def get_skill_connections():
    """Get all skill connections from the database"""
    try:
        if not hasattr(deps, 'kuzu_manager') or deps.kuzu_manager is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        connections = deps.kuzu_manager.get_all_skill_connections()
        return ConnectionsResponse(connections=connections, status="success")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving skill connections: {str(e)}")

@agent_router.post("/learning-path", response_model=LearningPathResponse)
async def find_learning_path(request: LearningPathRequest):
    """Find learning path between two skills"""
    try:
        if not hasattr(deps, 'kuzu_manager') or deps.kuzu_manager is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        path_objects = deps.kuzu_manager.find_learning_path_using_bfs(
            request.start_skill, 
            request.target_skill
        )
        
        # Convert skill IDs to skill details
        path_with_details = []
        for skill_id in path_objects:
            skill_info = deps.kuzu_manager.get_skill_by_id(skill_id)
            if skill_info:
                path_with_details.append(skill_info)
        
        return LearningPathResponse(path=path_with_details, status="success")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding learning path: {str(e)}")

@agent_router.get("/skill-prerequisites", response_model=PrerequisitesResponse)
async def get_skill_prerequisites(skill_name: str = Query(..., description="Name of the skill")):
    """Get prerequisites for a specific skill"""
    try:
        if not hasattr(deps, 'kuzu_manager') or deps.kuzu_manager is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        prerequisites = deps.kuzu_manager.get_skill_prerequisites_by_name(skill_name)
        return PrerequisitesResponse(prerequisites=prerequisites, status="success")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving prerequisites: {str(e)}")

@agent_router.get("/skill-details", response_model=SkillDetailsResponse)
async def get_skill_details(skill_name: str = Query(..., description="Name of the skill")):
    """Get detailed information about a specific skill"""
    try:
        if not hasattr(deps, 'kuzu_manager') or deps.kuzu_manager is None:
            raise HTTPException(status_code=500, detail="Database not initialized")
        
        skill_info = deps.kuzu_manager.get_skill_info(skill_name)
        return SkillDetailsResponse(skill=skill_info, status="success")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving skill details: {str(e)}")

# Add this router to your main app.py:
# from agentcore.render_app_endpoints import agent_router
# app.include_router(agent_router)
