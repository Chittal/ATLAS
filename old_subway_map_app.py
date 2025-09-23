from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from fastapi import Query

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


# Load data (supports legacy ai_track.json and new tracks_mapping_schema.json)
def load_track_data():
    # preferred = ['ai-tracks.json', 'tracks_mapping_schema.json', 'ai_track.json', 'ml-tracks.json']
    path = 'tracks/combined.json'
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    # Fallback empty graph if nothing found
    return {"nodes": [], "edges": []}

# Get track data
track_data = load_track_data()

def calculate_positions():
    """Tree layout positions from new schema (nodes/edges).
    - Left-to-right hierarchy: roots on the left, children to the right.
    - Nodes in the same depth are vertically spaced.
    """
    positions = {}
    nodes = track_data.get('nodes', [])
    edges = track_data.get('edges', [])
    if not nodes:
        return positions

    node_ids = [n['id'] for n in nodes]
    node_by_id = {n['id']: n for n in nodes}

    # Build adjacency and indegree
    adj = {nid: [] for nid in node_ids}
    indeg = {nid: 0 for nid in node_ids}
    for e in edges:
        u = e.get('from')
        v = e.get('to')
        if u in adj and v in indeg:
            adj[u].append(v)
            indeg[v] += 1

    # Roots: nodes with no incoming edges
    roots = [nid for nid in node_ids if indeg.get(nid, 0) == 0]
    if not roots:
        roots = [node_ids[0]]

    # Kahn's algorithm to compute depth (level)
    from collections import deque
    q = deque(roots)
    level = {nid: 0 for nid in roots}
    topo = []
    indeg_w = indeg.copy()
    while q:
        u = q.popleft()
        topo.append(u)
        for v in adj.get(u, []):
            # Max depth across parents
            level[v] = max(level.get(v, 0), level.get(u, 0) + 1)
            indeg_w[v] -= 1
            if indeg_w[v] == 0:
                q.append(v)

    # Any disconnected nodes that never enqueued
    for nid in node_ids:
        if nid not in level:
            level[nid] = 0

    # Group by level
    max_level = max(level.values()) if level else 0
    groups = [[] for _ in range(max_level + 1)]
    # preserve input order within each level
    for nid in node_ids:
        groups[level[nid]].append(nid)

    # Assign coordinates with truly spread-out Google Maps-like layout
    x_start, y_start = 300, 300
    x_step, y_step = 400, 600  # Much more spacing between levels and nodes
    
    import random
    random.seed(42)  # Consistent randomness
    
    # Calculate total available space - make it much larger
    total_width = (len(groups) - 1) * x_step + 600  # Much more padding
    total_height = max(len(group) for group in groups) * y_step + 800  # Much more height
    
    for depth, group in enumerate(groups):
        # Calculate base positions for this depth
        base_x = x_start + depth * x_step
        
        # Distribute nodes across a much larger vertical space
        if len(group) == 1:
            # Single node - center it in the available height
            base_y = y_start + total_height // 2
        else:
            # Multiple nodes - spread them across the full available height
            y_spacing = total_height / (len(group) + 1)  # +1 for padding
            base_y = y_start + y_spacing
        
        for idx, nid in enumerate(group):
            node = node_by_id[nid]
            
            # Calculate vertical position with much better distribution
            if len(group) == 1:
                final_y = base_y
            else:
                final_y = base_y + idx * y_spacing
            
            # Add much more significant random variations for true Google Maps spread
            x_variation = 120  # Much more horizontal spread
            y_variation = 100  # Much more vertical spread
            
            x_offset = random.uniform(-x_variation, x_variation)
            y_offset = random.uniform(-y_variation, y_variation)
            
            # Ensure nodes don't get too close to each other
            final_x = base_x + x_offset
            final_y = final_y + y_offset
            
            positions[nid] = {
                'x': final_x,
                'y': final_y,
                'name': node.get('name', nid),
                'level': node.get('level', '')
            }

    return positions

def get_track_colors():
    """Colors for audience types in the new schema"""
    return {
        "knowledge_workers": "#1f77b4",
        "technical_workers": "#2ca02c",
        "managers": "#ff7f0e"
    }

def normalize_audience_type(value: str) -> str:
    if not value:
        return "knowledge_workers"
    v = value.lower().strip()
    if v in ("knowledge", "conceptual", "knowledge_worker", "knowledge_workers"):  # blue
        return "knowledge_workers"
    if v in ("tech", "technical", "technical_worker", "technical_workers"):      # green
        return "technical_workers"
    if v in ("manager", "managers", "business", "strategy"):                     # orange
        return "managers"
    return v

def prepare_edges_with_color(edges: list) -> list:
    prepared = []
    for e in edges:
        etype = normalize_audience_type(e.get('audience_type', ''))
        new_e = dict(e)
        new_e['audience_type'] = etype
        new_e['color_key'] = etype
        prepared.append(new_e)
    return prepared

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Main page displaying the subway map"""
    positions = calculate_positions()
    colors = get_track_colors()
    
    # Prepare data for template (new schema only)
    edges = prepare_edges_with_color(track_data.get('edges', []))
    # Compute stage dimensions from positions with more bottom padding
    max_x = max((p['x'] for p in positions.values()), default=800)
    max_y = max((p['y'] for p in positions.values()), default=600)
    stage_width = max(2200, int(max_x + 600))  # Much wider for truly spread-out layout
    stage_height = max(2500, int(max_y + 800))  # Much taller for truly spread-out layout

    map_data = {
        "nodes": track_data.get('nodes', []),
        "edges": edges,
        "positions": positions,
        "colors": colors,
        "stage": {"width": stage_width, "height": stage_height},
        "title": "AI Learning Subway Map"
    }
    
    return templates.TemplateResponse("subway_map.html", {
        "request": request,
        "map_data": map_data
    })

@app.get("/api/map-data")
async def get_map_data():
    """API endpoint to get map data as JSON"""
    positions = calculate_positions()
    colors = get_track_colors()
    edges = prepare_edges_with_color(track_data.get('edges', []))
    max_x = max((p['x'] for p in positions.values()), default=800)
    max_y = max((p['y'] for p in positions.values()), default=600)
    stage_width = max(2200, int(max_x + 600))  # Much wider for truly spread-out layout
    stage_height = max(2500, int(max_y + 800))  # Much taller for truly spread-out layout
    return {
        "nodes": track_data.get('nodes', []),
        "edges": edges,
        "positions": positions,
        "colors": colors,
        "stage": {"width": stage_width, "height": stage_height},
        "title": "AI Learning Subway Map"
    }

# -----------------------------
# HTMX fragment endpoints
# -----------------------------

def _filter_for_user(user_type: str):
    positions = calculate_positions()
    colors = get_track_colors()

    # New schema (nodes/edges) only
    all_edges = prepare_edges_with_color(track_data.get('edges', []))
    if user_type == "all":
        edges = all_edges
    else:
        norm = normalize_audience_type(user_type)
        edges = [e for e in all_edges if e.get('audience_type') == norm]
    max_x = max((p['x'] for p in positions.values()), default=800)
    max_y = max((p['y'] for p in positions.values()), default=600)
    stage_width = max(2200, int(max_x + 600))  # Much wider for truly spread-out layout
    stage_height = max(2500, int(max_y + 800))  # Much taller for truly spread-out layout
    return {
        "nodes": track_data.get('nodes', []),
        "edges": edges,
        "positions": positions,
        "colors": colors,
        "stage": {"width": stage_width, "height": stage_height},
        "title": "AI Learning Subway Map"
    }

@app.get("/fragments/tracks", response_class=HTMLResponse)
async def fragment_tracks(request: Request, user: str = Query("all")):
    filtered = _filter_for_user(user)
    return templates.TemplateResponse("partials_tracks.svg", {"request": request, "map_data": filtered})

@app.get("/fragments/stations", response_class=HTMLResponse)
async def fragment_stations(request: Request, user: str = Query("all")):
    filtered = _filter_for_user(user)
    return templates.TemplateResponse("partials_stations.html", {"request": request, "map_data": filtered})

@app.get("/user/{user_type}")
async def get_user_path(user_type: str):
    """Return filtered edges for the given audience type (new schema)."""
    norm = normalize_audience_type(user_type)
    edges = prepare_edges_with_color(track_data.get('edges', []))
    filtered = [e for e in edges if e.get('audience_type') == norm]
    return {"user_type": norm, "nodes": track_data.get('nodes', []), "edges": filtered}

# -----------------------------
# Skills Graph Endpoints
# -----------------------------

@app.get("/skills-graph", response_class=HTMLResponse)
async def skills_graph_page(request: Request):
    """Skills graph visualization page"""
    return templates.TemplateResponse("skills_graph.html", {
        "request": request,
        "title": "Skills Learning Graph"
    })

@app.get("/api/skills-graph")
async def get_skills_graph_data():
    """Get skills data from Kuzu DB in Cytoscape.js format"""
    try:
        manager = get_kuzu_manager()
        # Get all skills
        skills = manager.get_all_skills()
        
        # Get all skill connections
        connections = manager.get_all_skill_connections()
        
        # Convert to Cytoscape.js format
        nodes = []
        edges = []
        
        # Add skill nodes
        for skill in skills:
            nodes.append({
                "data": {
                    "id": skill["id"],
                    "name": skill["name"],
                    "description": skill.get("description", ""),
                    "order_index": skill.get("order_index", 0)
                },
                "position": {
                    "x": skill.get("x", 0),
                    "y": skill.get("y", 0)
                }
            })
        
        # Add connection edges
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
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading skills data: {str(e)}")

@app.get("/api/skill-path")
async def get_skill_path(start_skill: str, end_skill: str):
    """Calculate learning path between two skills"""
    try:
        manager = get_kuzu_manager()
        # This would use your existing pathfinding logic
        # For now, return a simple path
        path = manager.find_learning_path(start_skill, end_skill)
        return {"path": path, "start": start_skill, "end": end_skill}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating path: {str(e)}")

@app.get("/api/skill-details/{skill_id}")
async def get_skill_details(skill_id: str):
    """Get detailed information about a specific skill"""
    try:
        manager = get_kuzu_manager()
        details = manager.get_skill_details(skill_id)
        return details
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading skill details: {str(e)}")

@app.get("/fragments/skills-graph", response_class=HTMLResponse)
async def fragment_skills_graph(request: Request):
    """HTMX fragment for skills graph container"""
    return templates.TemplateResponse("partials_skills_graph.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
