from kuzu_db_helper import KuzuSkillGraph

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
