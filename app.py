from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from fastapi import Query
from typing import List, Optional
from helper.populate_kuzu_db import KuzuSkillGraph

app = FastAPI(title="AI Learning Subway Map", description="Multi-user AI Learning Path Visualization")

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


@app.get("/", response_class=HTMLResponse)
async def roadmap_progression_page(request: Request):
    """Roadmap progression visualization page"""
    return templates.TemplateResponse("roadmap_progression.html", {
        "request": request,
        "title": "Learning Roadmap Progression"
    })

@app.get("/roadmap/flat", response_class=HTMLResponse)
async def skills_graph_flat_page(request: Request):
    """Flat skills graph (no levels) visualization page"""
    return templates.TemplateResponse("skills_graph_flat.html", {
        "request": request,
        "title": "Skills Graph (Flat)"
    })

def get_kuzu_manager():
    """Get or create Kuzu manager instance."""
    try:
        kuzu_manager = KuzuSkillGraph("skills_graph.db")
    except Exception as e:
        print(f"Warning: Could not connect to Kuzu database: {e}")
        raise e
    return kuzu_manager


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
