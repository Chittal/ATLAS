import asyncio
import logging
from datetime import datetime, timezone
from fastapi import Request, HTTPException, APIRouter
from deps import templates
import uuid
from helper.user_progress_helper import UserProgressHelper
from helper.helper import get_kuzu_manager
from fastapi.responses import RedirectResponse, HTMLResponse
from config import app_config
from helper.helper import get_current_user, require_owned_roadmap_path
from helper.agentcore import invoke_agent_runtime

router = APIRouter(
    prefix="",
    tags=["Learning Map"],
)


def get_agent(request: Request):
    """Lazily create the local route planning agent once and reuse it across requests."""
    if getattr(request.app.state, "agent", None) is None:
        from agents.personalized_route_planning_agent import PersonalizedRoutePlanningAgent
        # The agent runs in worker threads, so give it its own Kuzu connection (same database)
        request.app.state.agent = PersonalizedRoutePlanningAgent(
            kuzu_helper=request.app.state.kuzu_manager.with_own_connection()
        )
    return request.app.state.agent

@router.get("/api/skill/{skill_id}")
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

@router.get("/api/skills/{skill_name}/prerequisites")
async def get_skill_prerequisites(skill_name: str):
    """Get prerequisites for a specific skill."""
    try:
        manager = get_kuzu_manager()
        prerequisites = manager.get_skill_prerequisites_by_name(skill_name)
        return {
            "skill_name": skill_name,
            "prerequisites": prerequisites,
            "total_prerequisites": len(prerequisites)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting skill prerequisites: {str(e)}")

@router.get("/api/user/skills")
async def get_user_skills(request: Request):
    """Get all skills for the current user from their roadmap paths."""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get user's roadmap paths
        from helper.pocketbase_helper import get_pb_admin_client
        admin_pb = get_pb_admin_client()
        user_roadmap_paths = admin_pb.collection('user_roadmap_path').get_list(1, 100, {
            "filter": f"user_id = '{user.id}'"
        })
        
        if not user_roadmap_paths.items:
            return {"skills": []}
        
        # Get all roadmap_path_ids
        roadmap_path_ids = [path.roadmap_path_id for path in user_roadmap_paths.items]
        
        # Get skills from roadmap_path_skills table
        all_skills = []
        for roadmap_path_id in roadmap_path_ids:
            roadmap_skills = admin_pb.collection('roadmap_path_skills').get_list(1, 100, {
                "filter": f"roadmap_path_id = '{roadmap_path_id}'"
            })
            
            for roadmap_skill in roadmap_skills.items:
                # Get skill info from KuzuDB
                manager = get_kuzu_manager()
                skill_info = manager.get_skill_by_id(roadmap_skill.skill_id)
                
                if skill_info:
                    # Check if user has progress on this skill
                    progress_helper = UserProgressHelper(admin_pb)
                    skill_progress = progress_helper.get_user_skill_progress(user.id, roadmap_skill.skill_id)
                    
                    all_skills.append({
                        "id": skill_info["id"],
                        "name": skill_info["name"],
                        "description": skill_info.get("description", ""),
                        "order_index": skill_info.get("order_index", 0),
                        "progress": skill_progress,
                        "roadmap_path_id": roadmap_path_id
                    })
        
        # Remove duplicates and sort by order_index
        unique_skills = {}
        for skill in all_skills:
            if skill["id"] not in unique_skills:
                unique_skills[skill["id"]] = skill
        
        skills_list = list(unique_skills.values())
        skills_list.sort(key=lambda x: x.get("order_index", 0))
        
        return {"skills": skills_list}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user skills: {str(e)}")


@router.get("/api/skill/{skill_name}/learning-nodes")
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

@router.get("/api/skill/{skill_name}/learning-graph")
async def get_learning_graph_by_skill(request: Request, skill_name: str, user_roadmap_path_id: str | None = None, skill_id: str | None = None):
    """Get learning nodes and edges for a specific skill by name to create a connected graph."""
    # A saved path was named: it must belong to the logged-in user (checked before the try so 401/404 aren't turned into 500)
    owned_path = None
    if user_roadmap_path_id:
        from helper.pocketbase_helper import get_pb_admin_client
        owned_path = require_owned_roadmap_path(get_pb_admin_client(), get_current_user(request), user_roadmap_path_id)
    try:
        manager = get_kuzu_manager()
        learning_nodes = manager.get_learning_nodes_by_skill_name(skill_name)
        skill_edges = manager.get_skill_edges(skill_name)
        
        # Update learning_nodes_count in roadmap_path_skills table
        try:
            from helper.pocketbase_helper import get_pb_admin_client
            admin_pb = get_pb_admin_client()
            progress_helper = UserProgressHelper(admin_pb)
            # Resolve roadmap_path_id from user_roadmap_path_id if needed
            if owned_path is not None:
                roadmap_path_id = getattr(owned_path, 'roadmap_path_id', None)
                logging.debug(f"Resolved roadmap_path_id from user_roadmap_path_id {user_roadmap_path_id}: {roadmap_path_id}")

            if roadmap_path_id and skill_id:
                logging.debug(f"Updating learning nodes count by ids: {roadmap_path_id}, {skill_id}")
                progress_helper.update_learning_nodes_count_by_ids(roadmap_path_id, skill_id, len(learning_nodes))
            else:
                logging.debug(f"Updating learning nodes count by name: {skill_name}")
                progress_helper.update_learning_nodes_count(skill_name, len(learning_nodes))
            logging.debug(f"Learning nodes count updated for {skill_name}")
            logging.debug(f"Learning nodes count: {len(learning_nodes)}")
        except Exception as update_error:
            # Don't fail the main request if the count update fails
            logging.debug(f"Warning: Could not update learning nodes count for {skill_name}: {update_error}")
        
        return {
            "skill_name": skill_name,
            "learning_nodes": learning_nodes,
            "edges": skill_edges,
            "total_nodes": len(learning_nodes),
            "total_edges": len(skill_edges)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting learning graph: {str(e)}")

@router.get("/api/learning-node/{learning_node_id}/resources")
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

@router.get("/api/skill-path")
async def get_skill_path(request: Request, start: str = None, end: str = None, user_roadmap_path_id: str = None):
    """Get a learning path between two skills (by name) using KuzuDB graph, or from a user roadmap path.

    Returns a list of skill ids representing the path, and also the corresponding
    edges between consecutive skills for easy highlighting on the client.
    
    Parameters:
    - start, end: Use these to find a path between two skills by name
    - user_roadmap_path_id: Use this to get skills from a saved user roadmap path
    """
    # try:
    manager = get_kuzu_manager()
    
    # If user_roadmap_path_id is provided, get skills from the saved roadmap path
    if user_roadmap_path_id:
        # Ensure we have a fresh admin client
        from helper.pocketbase_helper import get_pb_admin_client
        admin_pb = get_pb_admin_client()
        require_owned_roadmap_path(admin_pb, get_current_user(request), user_roadmap_path_id)
        progress_helper = UserProgressHelper(admin_pb)
        skills = progress_helper.get_skills_from_user_roadmap_path(user_roadmap_path_id)
        logging.debug("%s %s", skills, "skills")
        
        if not skills:
            return {"path": [], "edges": []}
        
        # Convert skill IDs to full skill objects with names
        paths = []
        for skill in skills:
            skill_obj = manager.get_skill_by_id(skill["id"])
            logging.debug("%s %s", skill_obj, "skill_obj")
            if skill_obj:
                paths.append({
                    "id": skill["id"],
                    "name": skill_obj["name"],
                    "order_index": skill["order_index"],
                    "learning_nodes_count": skill["learning_nodes_count"]
                })
        
        # Create edges between consecutive skills
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
            "edges": edges,
            "source": "user_roadmap_path"
        }
    
    # Fallback to start/end parameters
    elif start and end:
        logging.debug("%s %s %s", start, end, "start, end")
        paths = manager.find_learning_path(start, end)
        logging.debug("%s %s", paths, "paths")
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
            "edges": edges,
            "source": "start_end_params"
        }
    else:
        raise HTTPException(status_code=400, detail="Either provide start/end parameters or user_roadmap_path_id")
        
    # except HTTPException:
    #     raise
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error finding skill path: {str(e)}")

def _path_edges(path_objects: list[dict]) -> list[dict]:
    """Edges between consecutive skills in a path, for highlighting on the client."""
    return [
        {"id": f"{a['id']}-{b['id']}", "source": a["id"], "target": b["id"]}
        for a, b in zip(path_objects, path_objects[1:])
    ]


def _build_chat_response(result: dict, fallback: bool = False) -> dict:
    """Turn an agent graph result into the JSON the chat widget expects."""
    assistant_messages = [m for m in (result.get("messages") or []) if m.get("role") == "assistant"]
    if result.get("status") == "success" and assistant_messages:
        ai_response = assistant_messages[-1]["content"]
    elif result.get("status") == "success":
        ai_response = "I'm sorry, I couldn't process your request."
    else:
        logging.error("Agent returned an error: %s", result.get("error"))
        ai_response = "I'm sorry, I couldn't process that request. Please try rephrasing it."

    metadata = {
        "category": result.get("category"),
        "step": result.get("step"),
        "status": result.get("status"),
    }
    if fallback:
        metadata["fallback"] = True

    response_data = {
        "ai_response": ai_response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_metadata": metadata,
    }

    path_objects = result.get("path_objects")
    if result.get("category") == "ROUTE_PLANNING" and path_objects:
        response_data["path_data"] = {"path": path_objects, "edges": _path_edges(path_objects)}
        logging.debug("Path data for highlighting: %s", response_data["path_data"])
    return response_data


async def _read_chat_message(request: Request) -> str:
    """Require a logged-in user and return the chat message from the request body."""
    if not get_current_user(request):
        raise HTTPException(status_code=401, detail="Not authenticated")
    body = await request.json()
    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    logging.debug("Chat message: %r", message)
    return message


async def _run_local_agent(request: Request, user_message: str) -> dict:
    """Run the local agent in a worker thread so its LLM calls don't block the event loop."""
    agent = get_agent(request)
    return await asyncio.to_thread(agent.execute_graph, user_message)


_CHAT_ERROR_RESPONSE = {
    "ai_response": "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
    "agent_metadata": {"category": "ERROR", "step": "error_handling", "status": "error"},
}


@router.post("/api/general/chat/agentcore")
async def general_chat_agentcore(request: Request):
    """Chat via the Bedrock AgentCore agent, falling back to the local agent if AgentCore fails."""
    user_message = await _read_chat_message(request)
    try:
        session_id = str(uuid.uuid4())
        result = await invoke_agent_runtime(user_message, session_id=session_id)
        agent_result = result.get("agent_result")
        if result.get("status") != "success" or not agent_result:
            raise RuntimeError(f"AgentCore returned no result: {result.get('message', 'unknown error')}")
        return _build_chat_response(agent_result)
    except Exception as e:
        logging.warning("AgentCore chat failed, falling back to local agent: %s", e)

    try:
        return _build_chat_response(await _run_local_agent(request, user_message), fallback=True)
    except Exception as e:
        logging.exception("Fallback agent also failed: %s", e)
        return {**_CHAT_ERROR_RESPONSE, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.post("/api/general/chat")
async def general_chat(request: Request):
    """Chat via the local LangGraph agent (used by the chat widget)."""
    user_message = await _read_chat_message(request)
    try:
        return _build_chat_response(await _run_local_agent(request, user_message))
    except Exception as e:
        logging.exception("Chat agent failed: %s", e)
        return {**_CHAT_ERROR_RESPONSE, "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/api/roadmap-progression")
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

@router.get("/api/roadmap-flat")
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

@router.get("/roadmap/progression", response_class=HTMLResponse)
async def roadmap_progression_page(request: Request):
    """Roadmap progression visualization page"""
    return templates.TemplateResponse("roadmap_progression.html", {
        "request": request,
        "title": "Roadmap"
    })

@router.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Home page with sidebar layout"""
    user = get_current_user(request)
    logging.debug(f"Main page access - User: {user}")  # Debug logging
    
    # Redirect to login if no authenticated user
    if not user:
        logging.debug("No user found, redirecting to login")  # Debug logging
        return RedirectResponse(url=f"{app_config.url_prefix}/login", status_code=302)
    
    logging.debug(f"User authenticated: {user.email}")  # Debug logging
    return templates.TemplateResponse("skills_graph.html", {
        "request": request,
        "user": user,
        "title": "Skills Graph"
    })

@router.get("/notes", response_class=HTMLResponse)
async def notes_content(request: Request):
    """Notes page - returns full layout for direct access, content-only for HTMX"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url=f"{app_config.url_prefix}/login", status_code=302)
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get("hx-request") == "true"
    
    if is_htmx:
        # Return just the content for HTMX navigation
        return templates.TemplateResponse("notes_content.html", {
            "request": request,
            "user": user
        })
    else:
        # Return full page layout for direct access (refresh) - reuse content template
        return templates.TemplateResponse("base.html", {
            "request": request,
            "user": user,
            "title": "Notes",
            "content_template": "notes_content.html"
        })

@router.get("/roadmaps", response_class=HTMLResponse)
async def roadmaps_content(request: Request):
    """Roadmaps page - returns full layout for direct access, content-only for HTMX"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url=f"{app_config.url_prefix}/login", status_code=302)
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get("hx-request") == "true"
    
    if is_htmx:
        # Return just the content for HTMX navigation
        return templates.TemplateResponse("roadmaps_content.html", {
            "request": request,
            "user": user
        })
    else:
        # Return full page layout for direct access (refresh) - reuse content template
        return templates.TemplateResponse("base.html", {
            "request": request,
            "user": user,
            "title": "Learning Paths",
            "content_template": "roadmaps_content.html"
        })

@router.get("/settings", response_class=HTMLResponse)
async def settings_content(request: Request):
    """Settings page - returns full layout for direct access, content-only for HTMX"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url=f"{app_config.url_prefix}/login", status_code=302)
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get("hx-request") == "true"
    
    if is_htmx:
        # Return just the content for HTMX navigation
        return templates.TemplateResponse("settings_content.html", {
            "request": request,
            "user": user
        })
    else:
        # Return full page layout for direct access (refresh) - reuse content template
        return templates.TemplateResponse("base.html", {
            "request": request,
            "user": user,
            "title": "Settings",
            "content_template": "settings_content.html"
        })

@router.get("/skills", response_class=HTMLResponse)
async def skills_content(request: Request):
    """Skills page - returns full layout for direct access, content-only for HTMX"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url=f"{app_config.url_prefix}/login", status_code=302)
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get("hx-request") == "true"
    
    if is_htmx:
        # Return just the content for HTMX navigation
        return templates.TemplateResponse("skills_content.html", {
            "request": request,
            "user": user
        })
    else:
        # Return full page layout for direct access (refresh) - reuse content template
        return templates.TemplateResponse("base.html", {
            "request": request,
            "user": user,
            "title": "Skills Overview",
            "content_template": "skills_content.html"
        })

@router.get("/profile", response_class=HTMLResponse)
async def profile_content(request: Request):
    """Profile page - returns full layout for direct access, content-only for HTMX"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url=f"{app_config.url_prefix}/login", status_code=302)
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get("hx-request") == "true"
    
    if is_htmx:
        # Return just the content for HTMX navigation
        return templates.TemplateResponse("profile_content.html", {
            "request": request,
            "user": user
        })
    else:
        # Return full page layout for direct access (refresh) - reuse content template
        return templates.TemplateResponse("base.html", {
            "request": request,
            "user": user,
            "title": "Profile",
            "content_template": "profile_content.html"
        })

@router.get("/learning-path", response_class=HTMLResponse)
async def learning_path_page(request: Request, start: str = None, end: str = None, user_roadmap_path_id: str | None = None):
    """Focused learning path visualization page showing only the highlighted path"""
    user = get_current_user(request)
    
    # Redirect to login if no authenticated user
    if not user:
        return RedirectResponse(url=f"{app_config.url_prefix}/login", status_code=302)
    
    # Set default values if neither user_roadmap_path_id nor start/end are provided
    if not user_roadmap_path_id and not start and not end:
        start = "data analyst"
        end = "ai agents"
    
    # Determine title based on the source
    if user_roadmap_path_id:
        title = "Learning Path: Saved Roadmap"
    else:
        title = f"Learning Path: {start} → {end}"
    
    return templates.TemplateResponse("learning_path.html", {
        "request": request,
        "start_skill": start,
        "end_skill": end,
        "roadmap_path_id": user_roadmap_path_id,
        "title": title,
        "user": user
    })


# API: List user's saved roadmap paths with skill counts
@router.get("/api/user/roadmaps")
async def get_user_roadmaps(request: Request):
    """Return roadmap paths saved by the current user, with number of skills per path.

    Data sources:
    - user_roadmap_path: mapping of user -> roadmap_path
    - roadmap_path_skills: used to count number of skills per roadmap_path
    """
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")

        # Ensure we have a fresh admin client
        from helper.pocketbase_helper import get_pb_admin_client
        admin_pb = get_pb_admin_client()
        progress_helper = UserProgressHelper(admin_pb)
        user_paths = progress_helper.get_user_roadmap_paths(user.id)
        logging.debug("%s %s", user_paths, "user_paths")

        roadmaps: list[dict] = []
        for path in user_paths:
            roadmap_path_id = path.get("roadmap_path_id")
            logging.debug("%s %s", roadmap_path_id, "roadmap_path_id")

            # Count skills for this roadmap path using totalItems (efficient)
            try:
                skills_page = admin_pb.collection('roadmap_path_skills').get_list(1, 1, {
                    "filter": f"roadmap_path_id = '{roadmap_path_id}'"
                })
                skill_count = getattr(skills_page, 'total_items', len(getattr(skills_page, 'items', [])))
            except Exception:
                skill_count = 0

            # Fetch roadmap path details for display (name, parent roadmap)
            try:
                rp = admin_pb.collection('roadmap_paths').get_one(roadmap_path_id)
                rp_name = getattr(rp, 'name', '')
                roadmap_id = getattr(rp, 'roadmap_id', '')
            except Exception:
                logging.debug("Error fetching roadmap path details")
                rp_name = ''
                roadmap_id = ''

            roadmaps.append({
                "user_roadmap_path_id": path.get("id"),
                "roadmap_path_id": roadmap_path_id,
                "roadmap_id": roadmap_id,
                "name": rp_name,
                "skill_count": skill_count,
                "progress": path.get("progress", 0),
                "created": path.get("created"),
                "updated": path.get("updated"),
            })

        return {"success": True, "roadmaps": roadmaps}
    except Exception as e:
        logging.debug(f"Error in get_user_roadmaps: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load user roadmaps: {str(e)}")
