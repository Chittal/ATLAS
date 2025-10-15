from operator import le
import kuzu
import json
import os
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

class KuzuSkillGraph:
    """
    KuzuDB integration for storing and managing learning roadmap skills as a graph database.
    """
    
    def __init__(self, db_path: str = "skills_graph.db"):
        """Initialize KuzuDB connection and create schema."""
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._create_schema()
    
    def _create_schema(self):
        """Create comprehensive graph schema for skills, nodes, and resources."""
        # Create Skill node table
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Skill(
                id STRING,
                name STRING,
                order_index INT64,
                PRIMARY KEY(id)
            )
        """)
        
        # Create LearningNode table for individual learning topics
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS LearningNode(
                id STRING,
                name STRING,
                description STRING,
                PRIMARY KEY(id)
            )
        """)
        
        # Create Resource table for learning resources
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Resource(
                id STRING,
                title STRING,
                url STRING,
                type STRING,
                PRIMARY KEY(id)
            )
        """)
        
        # Create relationship tables
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS BELONGS_TO(
                FROM LearningNode TO Skill
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS HAS_RESOURCE(
                FROM LearningNode TO Resource
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS PREREQUISITE(
                FROM LearningNode TO LearningNode,
                audience_type STRING
            )
        """)
        
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS SKILL_CONNECTION(
                FROM Skill TO Skill
            )
        """)
        
        print("KuzuDB comprehensive schema created successfully!")
    
    def load_skills_from_files(self, skills_list: List[str], data_dir: str = "data"):
        """Load skills from JSON roadmap files into KuzuDB."""
        order_index = 0
        skill_id_mapping = {}
        for skill in skills_list:
            print(skill)
            if isinstance(skill, list):
                # Handle nested skill groups
                for sub_skill in skill:
                    self._load_single_skill(sub_skill, data_dir, order_index, skill_id_mapping)
                    order_index += 1
            else:
                # Handle single skill
                self._load_single_skill(skill, data_dir, order_index, skill_id_mapping)
                order_index += 1
        return skill_id_mapping
    
    def _load_single_skill(self, skill_name: str, data_dir: str, order_index: int, skill_id_mapping: Dict[str, str]):
        """Load a single skill and its roadmap data from JSON file into KuzuDB."""
        file_name = skill_name.replace(" ", "-") + "_roadmap.json"
        file_path = os.path.join(data_dir, file_name)
        
        if not os.path.exists(file_path):
            print(f"Warning: Roadmap file not found for skill: {skill_name} at {file_path}")
            return skill_id_mapping
        # try:
        with open(file_path, "r", encoding="utf-8") as f:
            skill_data = json.load(f)
        
        # Insert skill node
        skill_id = str(uuid.uuid4())
        skill_id_mapping[skill_name] = skill_id
        self.conn.execute("""
            MERGE (s:Skill {id: $skill_id, name: $name, order_index: $order_index})
        """, parameters={
            "skill_id": skill_id,
            "name": skill_name,
            "order_index": order_index
        })
        
        # Insert learning nodes and their relationships
        nodes = skill_data.get("nodes", [])
        learning_node_mapping = {}
        for node in nodes:
            learning_node_id = self._insert_learning_node(node, skill_id)
            learning_node_mapping[node["id"]] = learning_node_id
        
        # Insert edges (relationships between nodes)
        edges = skill_data.get("edges", [])
        for edge in edges:
            self._insert_edge(edge, skill_id, learning_node_mapping)
        
        print(f"Loaded skill: {skill_name} with {len(nodes)} nodes and {len(edges)} edges")
        return skill_id_mapping
        # except Exception as e:
        #     print(f"Error loading skill {skill_name}: {str(e)}")
        #     # Still create the skill node even if there's an error
        #     # skill_id = f"skill_{skill_name.replace(' ', '_')}"
        #     # self.conn.execute("""
        #     #     MERGE (s:Skill {id: $skill_id, name: $name, order_index: $order_index})
        #     # """, parameters={
        #     #     "skill_id": skill_id,
        #     #     "name": skill_name,
        #     #     "order_index": order_index
        #     # })
        #     return skill_id_mapping
    
    def handle_learning_node_insertion(self, node_name: str, description: str, original_node_id: str):
        result = self.conn.execute("""
            MATCH (n:LearningNode) 
            WHERE n.name = $name AND n.description = $description
            RETURN n.id LIMIT 1
        """, parameters={
            "name": node_name,
            "description": description
        })
        
        if result.has_next():
            existing_id = result.get_next()[0]
            print(f"Case 1: Found existing node with same name+description, using ID: {existing_id}")
            return existing_id, False
        
        # Case 2: Check if original ID exists but with different name/description
        result = self.conn.execute("""
            MATCH (n:LearningNode) 
            WHERE n.id = $id
            RETURN n.name, n.description
        """, parameters={"id": original_node_id})
        
        if result.has_next():
            existing_name, existing_desc = result.get_next()
            if existing_name != node_name or existing_desc != description:
                # ID exists but content is different, create new ID
                new_id = str(uuid.uuid4())
                self.conn.execute("""
                    CREATE (n:LearningNode {
                        id: $id, 
                        name: $name, 
                        description: $description
                    })
                """, parameters={
                    "id": new_id,
                    "name": node_name,
                    "description": description
                })
                print(f"Case 2: ID exists with different content, created new ID: {new_id}")
                return new_id, True
            else:
                # ID exists with same content
                print(f"Case 2b: ID exists with same content, using original ID: {original_node_id}")
                return original_node_id, False
        
        # Case 3: Everything is new, use original ID
        self.conn.execute("""
            CREATE (n:LearningNode {
                id: $id, 
                name: $name, 
                description: $description
            })
        """, parameters={
            "id": original_node_id,
            "name": node_name,
            "description": description
        })
        # print(f"Case 3: All new, created node with original ID: {original_node_id}")
        return original_node_id, True
    
    def handle_resource(self, title, url, resource_type):
        """
        Handle Resource with your specific case:
        If title + url + type exists -> return old id
        Else create new entry with new id
        
        Returns: (resource_id, is_new_resource)
        """
        
        # Check if resource already exists
        result = self.conn.execute("""
            MATCH (r:Resource) 
            WHERE r.title = $title AND r.url = $url AND r.type = $type
            RETURN r.id LIMIT 1
        """, parameters={
            "title": title,
            "url": url,
            "type": resource_type
        })
        
        if result.has_next():
            existing_id = result.get_next()[0]
            # print(f"Resource exists, using ID: {existing_id}")
            return existing_id, False
        
        # Create new resource
        new_resource_id = str(uuid.uuid4())
        self.conn.execute("""
            CREATE (r:Resource {
                id: $id, 
                title: $title, 
                url: $url, 
                type: $type
            })
        """, parameters={
            "id": new_resource_id,
            "title": title,
            "url": url,
            "type": resource_type
        })
        # print(f"Created new resource with ID: {new_resource_id}")
        return new_resource_id, True
    
    def _insert_learning_node(self, node: Dict[str, Any], skill_id: str):
        """Insert a learning node and its resources into KuzuDB."""
        original_node_id = node.get("id")
        # Create unique node ID by prefixing with skill name to avoid conflicts across roadmaps
        # unique_node_id = f"{skill_id}_{original_node_id}"
        node_name = node.get("name", "")
        description = ""
        resources = []
        
        if "resources" in node:
            resources_data = node["resources"]
            # get the description from the resources data
            description = resources_data.get("description", "")
            resources = resources_data.get("resources", [])
        
        learning_node_id, is_new = self.handle_learning_node_insertion(node_name, description, original_node_id)
        # Create relationship between node and skill
        self.conn.execute("""
            MATCH (n:LearningNode {id: $node_id}), (s:Skill {id: $skill_id})
            MERGE (n)-[:BELONGS_TO]->(s)
        """, parameters={
            "node_id": learning_node_id,
            "skill_id": skill_id
        })
        
        # Insert resources "node_id": original_node_id, node_id: $node_id
        for i, resource in enumerate(resources):
            resource_id, is_new = self.handle_resource(resource.get("title", ""), resource.get("url", ""), resource.get("type", ""))
            
            # Create relationship between node and resource
            self.conn.execute("""
                MATCH (n:LearningNode {id: $node_id}), (r:Resource {id: $resource_id})
                MERGE (n)-[:HAS_RESOURCE]->(r)
            """, parameters={
                "node_id": learning_node_id,
                "resource_id": resource_id
            })
        return learning_node_id
    
    def _insert_edge(self, edge: Dict[str, Any], skill_id: str, learning_node_mapping: Dict[str, str]):
        """Insert an edge (relationship) between learning nodes."""
        from_node_id = learning_node_mapping.get(edge.get("source"))
        to_node_id = learning_node_mapping.get(edge.get("target"))
        audience_type = edge.get("audience_type", "")
        
        if from_node_id and to_node_id:
            # Convert original node IDs to unique IDs by prefixing with skill_id
            # unique_from_id = f"{skill_id}_{from_node}"
            # unique_to_id = f"{skill_id}_{to_node}"
            
            self.conn.execute("""
                MATCH (from:LearningNode {id: $from_id}), (to:LearningNode {id: $to_id})
                MERGE (from)-[:PREREQUISITE {audience_type: $audience_type}]->(to)
            """, parameters={
                "from_id": from_node_id,
                "to_id": to_node_id,
                "audience_type": audience_type
            })
    
    def add_skill_connection(self, from_skill: str, to_skill: str):
        """Add a connection between two skills."""
        self.conn.execute("""
            MATCH (from:Skill {id: $from_id}), (to:Skill {id: $to_id})
            MERGE (from)-[:SKILL_CONNECTION]->(to)
        """, parameters={
            "from_id": from_skill,
            "to_id": to_skill
        })
        
        print(f"Added skill connection: {from_skill} -> {to_skill}")
    
    def add_skill_connections_from_progression(self, skill_id_mapping: Dict[str, str]):
        """Add skill connections based on logical learning progression from the skills list."""
        # Define the logical learning progression connections
        connections = [
            # Foundation skills
            ("computer science", "datastructures and algorithms"),
            ("datastructures and algorithms", "python"),
            ("datastructures and algorithms", "java"),
            ("datastructures and algorithms", "cpp"),
            ("datastructures and algorithms", "javascript"),
            
            # Programming fundamentals to version control
            ("python", "git github"),
            ("java", "git github"),
            ("cpp", "git github"),
            ("javascript", "git github"),
            
            # Version control to databases
            ("git github", "frontend"),
            ("git github", "backend"),
            
            # Programming languages to web development
            ("javascript", "frontend"),
            ("javascript", "backend"),
            ("python", "backend"),
            ("java", "backend"),
            ("cpp", "backend"),
            
            # Web development progression
            ("frontend", "react"),
            ("frontend", "angular"),
            ("frontend", "vue"),
            
            # Backend technologies
            ("backend", "sql"),
            ("backend", "nodejs"),
            ("backend", "php"),
            ("backend", "spring boot"),
            ("backend", "aspnet core"),
            ("javascript", "angular"),
            ("javascript", "vue"),
            ("javascript", "react"),
            ("javascript", "nodejs"),
            ("java", "spring boot"),
            ("cpp", "aspnet core"),
            
            # Full stack development
            ("frontend", "full stack"),
            ("backend", "full stack"),
            ("react", "full stack"),
            ("nodejs", "full stack"),
            ("full stack", "nextjs"),
            
            # Advanced web technologies
            ("javascript", "typescript"),
            ("react", "typescript"),
            ("typescript", "graphql"),
            ("backend", "graphql"),
            
            # Databases
            ("sql", "mongodb"),
            ("sql", "postgresql dba"),
            ("sql", "redis"),
            
            # Mobile development
            ("javascript", "react native"),
            ("react", "react native"),
            ("react native", "ios"),
            ("react native", "android"),
            ("java", "android"),
            ("cpp", "android"),
            ("javascript", "flutter"),
            
            # Game development
            ("cpp", "game developer"),
            ("cpp", "server side game developer"),
            ("javascript", "game developer"),
            
            # Design and UX
            ("frontend", "design system"),
            ("frontend", "ux design"),
            ("css", "design system"),
            ("css", "ux design"),
            
            # Quality and processes
            ("python", "code review"),
            ("java", "code review"),
            ("javascript", "code review"),
            ("git github", "code review"),
            ("code review", "qa"),
            
            # Data and analytics
            ("python", "bi analyst"),
            ("python", "data analyst"),
            ("sql", "bi analyst"),
            ("sql", "data analyst"),
            ("data analyst", "data engineer"),
            ("python", "data engineer"),
            ("data engineer", "aws"),
            
            # DevOps and infrastructure
            ("python", "devops"),
            ("java", "devops"),
            ("javascript", "devops"),
            ("devops", "docker"),
            ("devops", "linux"),
            ("docker", "kubernetes"),
            ("kubernetes", "terraform"),
            ("kubernetes", "cloudflare"),
            
            # Security
            ("devops", "cyber security"),
            ("python", "cyber security"),
            ("cyber security", "ai red teaming"),
            
            # Modern languages
            ("python", "golang"),
            ("python", "rust"),
            ("cpp", "rust"),
            ("golang", "blockchain"),
            ("rust", "blockchain"),
            
            # System design
            ("backend", "system design"),
            ("full stack", "system design"),
            ("system design", "software design architecture"),
            
            # Leadership and management
            ("software design architecture", "software architect"),
            ("software architect", "engineering manager"),
            ("engineering manager", "product manager"),
            ("software architect", "devrel"),
            ("software architect", "technical writer"),
            
            # AI and Machine Learning
            ("python", "machine learning"),
            ("data analyst", "machine learning"),
            ("machine learning", "prompt engineering"),
            ("machine learning", "mlops"),
            ("python", "mlops"),
            ("devops", "mlops"),
            ("mlops", "ai engineer"),
            ("machine learning", "ai engineer"),
            ("ai engineer", "ai data scientist"),
            ("ai data scientist", "ai agents"),
        ]
        
        # Add all connections
        for from_skill, to_skill in connections:
            try:
                self.add_skill_connection(skill_id_mapping[from_skill], skill_id_mapping[to_skill])
            except Exception as e:
                print(f"Warning: Could not add connection {from_skill} -> {to_skill}: {str(e)}")
        
        print(f"Added {len(connections)} skill connections based on learning progression")
    
    def get_skill_info(self, skill_name: str) -> Dict[str, Any]:
        """Retrieve information for a specific skill."""
        
        # Get skill information
        result = self.conn.execute("""
            MATCH (s:Skill {name: $skill_name})
            RETURN s.id as id, s.order_index as order_index
        """, parameters={"skill_name": skill_name})
        
        skill_info = result.get_next()
        if not skill_info:
            return {"error": f"Skill '{skill_name}' not found"}
        
        return {
            "id": skill_info[0],
            "order_index": skill_info[1]
        }
    
    def get_all_skills(self) -> List[Dict[str, Any]]:
        """Get all skills ordered by their index."""
        result = self.conn.execute("""
            MATCH (s:Skill)
            RETURN s.id as id, s.name as name, s.order_index as order_index
            ORDER BY s.order_index
        """)
        
        skills = []
        while result.has_next():
            row = result.get_next()
            skills.append({
                "id": row[0],
                "name": row[1],
                "order_index": row[2]
            })
        
        return skills
    
    def get_skill_roadmap(self, skill_name: str) -> Dict[str, Any]:
        """Retrieve a complete roadmap for a specific skill."""
        skill_id = f"skill_{skill_name.replace(' ', '_')}"
        
        # Get skill information
        result = self.conn.execute("""
            MATCH (s:Skill {id: $skill_id})
            RETURN s.name as name, s.order_index as order_index
        """, parameters={"skill_id": skill_id})
        
        skill_info = result.get_next()
        if not skill_info:
            return {"error": f"Skill '{skill_name}' not found"}
        
        # Get all learning nodes for this skill
        result = self.conn.execute("""
            MATCH (s:Skill {id: $skill_id})<-[:BELONGS_TO]-(n:LearningNode)
            RETURN n.id as id, n.name as name, n.description as description
            ORDER BY n.name
        """, parameters={"skill_id": skill_id})
        
        nodes = []
        while result.has_next():
            row = result.get_next()
            nodes.append({
                "id": row[0],
                "name": row[1],
                "description": row[2]
            })
        
        # Get all edges for this skill
        result = self.conn.execute("""
            MATCH (s:Skill {id: $skill_id})<-[:BELONGS_TO]-(from:LearningNode)-[:PREREQUISITE]->(to:LearningNode)-[:BELONGS_TO]->(s)
            RETURN from.id as from_id, to.id as to_id
        """, parameters={"skill_id": skill_id})
        
        edges = []
        while result.has_next():
            row = result.get_next()
            edges.append({
                "from": row[0],
                "to": row[1],
                "audience_type": "general"  # Default audience type
            })
        
        return {
            "skill": skill_info[0],
            "order_index": skill_info[1],
            "nodes": nodes,
            "edges": edges
        }
    
    def get_skill_connections(self, skill_name: str) -> Dict[str, List[str]]:
        """Get skills connected to the given skill (both incoming and outgoing)."""
        skill_id = f"skill_{skill_name.replace(' ', '_')}"
        
        # Get outgoing connections (skills this skill connects to)
        result = self.conn.execute("""
            MATCH (s:Skill {id: $skill_id})-[:SKILL_CONNECTION]->(connected:Skill)
            RETURN connected.name as name
        """, parameters={"skill_id": skill_id})
        
        outgoing = []
        while result.has_next():
            row = result.get_next()
            outgoing.append(row[0])
        
        # Get incoming connections (skills that connect to this skill)
        result = self.conn.execute("""
            MATCH (connected:Skill)-[:SKILL_CONNECTION]->(s:Skill {id: $skill_id})
            RETURN connected.name as name
        """, parameters={"skill_id": skill_id})
        
        incoming = []
        while result.has_next():
            row = result.get_next()
            incoming.append(row[0])
        
        return {
            "incoming": incoming,
            "outgoing": outgoing
        }
    
    def get_all_skills(self) -> List[Dict]:
        """Get all skills from the database."""
        result = self.conn.execute("""
            MATCH (s:Skill)
            RETURN s.id as id, s.name as name, s.order_index as order_index
        """)
        
        skills = []
        while result.has_next():
            row = result.get_next()
            skills.append({
                "id": row[0],
                "name": row[1],
                "description": f"Learn {row[1]} skills and concepts",
                "order_index": row[2]
            })
        
        return skills
    
    def get_all_skill_connections(self) -> List[Dict]:
        """Get all skill connections from the database."""
        result = self.conn.execute("""
            MATCH (from:Skill)-[:SKILL_CONNECTION]->(to:Skill)
            RETURN from.id as from_skill, to.id as to_skill
        """)
        
        connections = []
        while result.has_next():
            row = result.get_next()
            connections.append({
                "from_skill": row[0],
                "to_skill": row[1],
                "relationship_type": "prerequisite",  # Default relationship type
                "weight": 1  # Default weight
            })
        
        return connections
    
    def get_skill_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Get a single skill by its id."""
        result = self.conn.execute("""
            MATCH (s:Skill {id: $id})
            RETURN s.id as id, s.name as name, s.order_index as order_index
            LIMIT 1
        """, parameters={"id": skill_id})
        if result.has_next():
            row = result.get_next()
            return {
                "id": row[0],
                "name": row[1],
                "description": f"Learn {row[1]} skills and concepts",
                "order_index": row[2]
            }
        return None

    def get_skill_prerequisites(self, skill_id: str) -> List[Dict[str, Any]]:
        """Get prerequisite skills (incoming skill connections)."""
        result = self.conn.execute("""
            MATCH (pre:Skill)-[:SKILL_CONNECTION]->(s:Skill {id: $id})
            RETURN pre.id as id, pre.name as name
        """, parameters={"id": skill_id})
        skills: List[Dict[str, Any]] = []
        while result.has_next():
            row = result.get_next()
            skills.append({
                "id": row[0],
                "name": row[1]
            })
        return skills

    def get_skill_prerequisites_by_name(self, skill_name: str) -> List[Dict[str, Any]]:
        """Get prerequisite skills (incoming skill connections)."""
        try:
            skill_id = self.get_skill_info(skill_name)["id"]
            result = self.conn.execute("""
                MATCH (pre:Skill)-[:SKILL_CONNECTION]->(s:Skill {id: $id})
                RETURN pre.id as id, pre.name as name
            """, parameters={"id": skill_id})
            skills: List[Dict[str, Any]] = []
            while result.has_next():
                row = result.get_next()
                skills.append({
                    "id": row[0],
                    "name": row[1]
                })
            return skills
        except Exception as e:
            print(f"Error getting skill prerequisites by name: {e}")
            return []

    def get_skill_next_skills(self, skill_id: str) -> List[Dict[str, Any]]:
        """Get next skills (outgoing skill connections)."""
        result = self.conn.execute("""
            MATCH (s:Skill {id: $id})-[:SKILL_CONNECTION]->(next:Skill)
            RETURN next.id as id, next.name as name
        """, parameters={"id": skill_id})
        skills: List[Dict[str, Any]] = []
        while result.has_next():
            row = result.get_next()
            skills.append({
                "id": row[0],
                "name": row[1]
            })
        return skills

    def get_roadmap_progression(self) -> Dict[str, Any]:
        """Get skills from KuzuDB in their stored order for roadmap visualization."""
        # Get all skills from database in their stored order
        all_skills = self.get_all_skills()
        
        # Create a simple linear progression with skills in database order
        # Group skills into levels of 4-6 skills each for better visualization
        skills_per_level = 5
        organized_skills = {}
        level_names = []
        
        for i in range(0, len(all_skills), skills_per_level):
            level_skills = all_skills[i:i + skills_per_level]
            level_name = f"Level {len(level_names) + 1}"
            level_names.append(level_name)
            organized_skills[level_name] = level_skills
        
        # Get skill connections for visualization
        connections = self.get_all_skill_connections()
        
        return {
            "levels": organized_skills,
            "level_names": level_names,
            "connections": connections,
            "total_skills": len(all_skills),
            "total_levels": len(organized_skills)
        }

    def find_learning_path(self, start_skill: str, end_skill: str) -> List[Dict[str, str]]:
        """Find a learning path between two skills using KuzuDB shortest path."""
        res = self.conn.execute(
            """
            MATCH path = (s1:Skill {name: $start_skill})-[:SKILL_CONNECTION*1..10]-(s2:Skill {name: $end_skill})
            RETURN path
            ORDER BY length(path)
            LIMIT 1;
            """,
            parameters={"start_skill": start_skill, "end_skill": end_skill}
        )
        path: List[Dict[str, str]] = []
        while res.has_next():
            row = res.get_next()
            for node in row[0]["_nodes"]:
                path.append({"id": node["id"], "name": node["name"]})
        print("=================================")
        print("Path objects:", path)
        print("=================================")
        return path
    
    def find_learning_path_using_bfs(self, start_skill: str, end_skill: str) -> List[str]:
        """Find a learning path between two skills using BFS."""
        # Resolve skill names to IDs from KuzuDB
        def _get_id_by_name(name: str) -> Optional[str]:
            res = self.conn.execute(
                """
                MATCH (s:Skill)
                WHERE toLower(s.name) = toLower($name)
                RETURN s.id LIMIT 1
                """,
                parameters={"name": name}
            )
            if res.has_next():
                return res.get_next()[0]
            return None

        start_id = _get_id_by_name(start_skill)
        end_id = _get_id_by_name(end_skill)
        print(start_id, end_id, "start_id, end_id")
        if not start_id or not end_id:
            print(f"Skill not found: {start_skill} or {end_skill}")
            return []
        
        # Fall back to Python BFS over directed edges
        from collections import deque

        def get_neighbors(skill_id: str) -> List[str]:
            res = self.conn.execute(
                """
                MATCH (s:Skill {id: $id})-[:SKILL_CONNECTION]->(n:Skill)
                RETURN n.id
                """,
                parameters={"id": skill_id}
            )
            neighbors: List[str] = []
            while res.has_next():
                row = res.get_next()
                neighbors.append(row[0])
            return neighbors

        queue: deque[str] = deque([start_id])
        visited: set[str] = {start_id}
        parent: dict[str, Optional[str]] = {start_id: None}

        found: bool = False
        while queue:
            current = queue.popleft()
            if current == end_id:
                found = True
                break
            for neighbor in get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)

        if not found:
            return []

        # Reconstruct path from end_id back to start_id
        path: List[str] = []
        node = end_id
        while node is not None:
            path.append(node)
            node = parent.get(node)
        path.reverse()
        return path
        # except Exception:
        #     # Fallback to empty path if KuZU shortestPath is not available
        #     return []
    
    def search_skills(self, query: str, category: str = None, difficulty: str = None) -> List[Dict]:
        """Search skills by name."""
        result = self.conn.execute("""
            MATCH (s:Skill)
            WHERE s.name CONTAINS $query
            RETURN s.id as id, s.name as name, s.order_index as order_index
        """, parameters={"query": query})
        
        skills = []
        while result.has_next():
            row = result.get_next()
            skills.append({
                "id": row[0],
                "name": row[1],
                "description": f"Learn {row[1]} skills and concepts",
                "order_index": row[2]
            })
        
        return skills

    def execute_cypher_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute a Cypher query and return the results."""
        result = self.conn.execute(query, parameters=parameters)
        return result
    
    def get_learning_nodes_by_skill_name(self, skill_name: str) -> List[Dict[str, Any]]:
        """Get learning nodes for a specific skill by name."""
        try:
            result = self.conn.execute(f"""
                MATCH (s:Skill)<-[:BELONGS_TO]-(l:LearningNode)
                WHERE s.name = $skill_name
                OPTIONAL MATCH path = (start:LearningNode)-[:PREREQUISITE*0..]->(l)
                WHERE (start)-[:BELONGS_TO]->(s)
                AND NOT (start)<-[:PREREQUISITE]-(:LearningNode)-[:BELONGS_TO]->(s)
                WITH l, MAX(length(path)) as depth
                RETURN depth, l.id, l.name, l.description
                ORDER BY depth, l.name;
            """, parameters={"skill_name": skill_name})
            learning_nodes: List[Dict[str, Any]] = []
            while result.has_next():
                row = result.get_next()
                learning_nodes.append({
                    "depth": row[0] if row[0] is not None else 0,
                    "id": row[1],
                    "name": row[2],
                    "description": row[3] if row[3] is not None else ""
                })
            return learning_nodes
        except Exception as e:
            print(f"Error getting learning nodes by skill name: {e}")
            return []

    def get_resources_by_learning_node_id(self, learning_node_id: str) -> List[Dict[str, Any]]:
        """Get prerequisite skills (incoming skill connections)."""
        try:
            result = self.conn.execute(f"""
                MATCH (l:LearningNode {id: $learning_node_id})-[:HAS_RESOURCE]->(r:Resource)
                RETURN r.id, r.title, r.url, r.type
                ORDER BY r.title;
            """, parameters={"learning_node_id": learning_node_id})
            resources: List[Dict[str, Any]] = []
            while result.has_next():
                row = result.get_next()
                resources.append({
                    "id": row[0],
                    "title": row[1],
                    "url": row[2],
                    "type": row[3]
                })
            return resources
        except Exception as e:
            print(f"Error getting resources by learning node id: {e}")
            return []
    
    def close(self):
        """Close the database connection."""
        self.conn.close()

# Initialize the skill graph
def initialize_skill_graph():
    """ Initialize and populate the KuzuDB skill graph with all roadmap data. """
    skills = [
        "computer science", "datastructures and algorithms", 
        ["python", "java", "cpp", "javascript"], 
        ["git github", "sql"], 
        ["frontend", "backend"], 
        ["react", "angular", "vue"], 
        ["nodejs", "php", "spring boot", "aspnet core"], 
        ["full stack", "nextjs"], 
        ["typescript", "graphql"], 
        ["mongodb", "postgresql dba", "redis"], 
        ["android", "ios", "flutter", "react native"], 
        ["game developer", "server side game developer"], 
        ["design system", "ux design"], 
        ["code review", "qa"], 
        ["bi analyst", "data analyst"], 
        ["data engineer", "aws"], 
        ["devops", "docker", "linux"], 
        ["kubernetes", "terraform", "cloudflare"], 
        ["cyber security", "ai red teaming"], 
        ["blockchain", "golang", "rust"], 
        ["system design", "software design architecture"], 
        ["software architect", "engineering manager", "product manager", "devrel", "technical writer"], 
        ["machine learning", "prompt engineering"], 
        ["mlops", "ai engineer"], 
        ["ai data scientist", "ai agents"]
    ]
    # Create and populate the graph
    skill_graph = KuzuSkillGraph()
    skill_id_mapping = skill_graph.load_skills_from_files(skills)
    
    # Add skill connections based on logical learning progression
    print("\nAdding skill connections from basic to advanced...")

    skill_graph.add_skill_connections_from_progression(skill_id_mapping)
    
    print("Skill graph initialized successfully!")
    return skill_graph

# Example usage
if __name__ == "__main__":
    # Initialize the graph
    graph = initialize_skill_graph()
    
    # Example queries
    print("\nAll skills:")
    all_skills = graph.get_all_skills()
    for skill in all_skills[:10]:  # Show first 10
        print(f"- {skill['name']} (order: {skill['order_index']})")
    
    print("\nPython skill info:")
    python_info = graph.get_skill_info("python")
    if "error" not in python_info:
        print(f"Skill: {python_info['name']} (order: {python_info['order_index']})")
    
    # Example: Show skill connections for Python
    print("\nPython skill connections:")
    python_connections = graph.get_skill_connections("python")
    print(f"Incoming: {python_connections['incoming']}")
    print(f"Outgoing: {python_connections['outgoing']}")
    
    # Example: Show skill connections for JavaScript
    print("\nJavaScript skill connections:")
    js_connections = graph.get_skill_connections("javascript")
    print(f"Incoming: {js_connections['incoming']}")
    print(f"Outgoing: {js_connections['outgoing']}")
    
    print("\nPython roadmap details:")
    python_roadmap = graph.get_skill_roadmap("python")
    if "error" not in python_roadmap:
        print(f"Skill: {python_roadmap['skill']}")
        print(f"Learning nodes: {len(python_roadmap['nodes'])}")
        print(f"Prerequisites: {len(python_roadmap['edges'])}")
        if python_roadmap['nodes']:
            print(f"First node: {python_roadmap['nodes'][0]['name']}")
    
    # Close the connection
    graph.close()
