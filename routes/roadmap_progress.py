from fastapi import Request, HTTPException, APIRouter
from deps import pb
from helper.user_progress_helper import UserProgressHelper
from helper.helper import get_current_user

router = APIRouter(
    prefix="",
    tags=["Roadmap Progress"],
)

@router.post("/api/route-planning/start-learning")
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
        
        progress_helper = UserProgressHelper(pb)
        
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

@router.get("/api/user/progress")
async def get_user_progress(request: Request):
    """Get user's learning progress"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Use admin client for reading user progress
        progress_helper = UserProgressHelper(pb)
        user_paths = progress_helper.get_user_roadmap_paths(user.id)
        
        return {
            "success": True,
            "user_paths": user_paths
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user progress: {str(e)}")

@router.post("/api/user/progress/update")
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
        
        progress_helper = UserProgressHelper(pb)
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

@router.post("/api/learning-node/complete")
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
        
        progress_helper = UserProgressHelper(pb)
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

@router.post("/api/learning-node/incomplete")
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
        
        progress_helper = UserProgressHelper(pb)
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

@router.get("/api/learning-node/progress")
async def get_learning_node_progress(request: Request, user_roadmap_path_id: str = None):
    """Get user's learning node progress"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        progress_helper = UserProgressHelper(pb)
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
