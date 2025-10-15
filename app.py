from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from llm.groq import call_groq_model
from helper.kuzu_db_helper import KuzuSkillGraph
from agents.personalized_route_planning_agent import PersonalizedRoutePlanningAgent

from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

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
async def skills_graph_flat_page(request: Request):
    """Flat skills graph (no levels) visualization page"""
    return templates.TemplateResponse("skills_graph_flat.html", {
        "request": request,
        "title": "Roadmap Kuzu Graph Style"
    })

@app.get("/learning-path", response_class=HTMLResponse)
async def learning_path_page(request: Request, start: str = "data analyst", end: str = "ai agents"):
    """Focused learning path visualization page showing only the highlighted path"""
    return templates.TemplateResponse("learning_path.html", {
        "request": request,
        "start_skill": start,
        "end_skill": end,
        "title": f"Learning Path: {start} → {end}"
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
async def get_learning_graph_by_skill(skill_name: str):
    """Get learning nodes and edges for a specific skill by name to create a connected graph."""
    try:
        manager = get_kuzu_manager()
        learning_nodes = manager.get_learning_nodes_by_skill_name(skill_name)
        skill_edges = manager.get_skill_edges(skill_name)
        
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

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint"""
    print("TEST ENDPOINT HIT!")
    return {"message": "Test endpoint working!", "timestamp": "2024-01-01T00:00:00Z"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
