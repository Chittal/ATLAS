import json
import os
import re

from pathlib import Path


def collapse_dashes(text: str) -> str:
    """Replace multiple consecutive dashes with a single dash."""
    return re.sub(r'-+', '-', text)


def generate_content_file_name(text: str) -> str:
    # Keep only letters and spaces
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    # Lowercase
    text = text.lower()
    # Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text).strip()
    # Replace spaces with '-'
    return text.replace(' ', '-')


def get_content_key(filename: str):
    try:
        filename = filename.split(".md")[0].split("@")[1]
    except:
        filename = filename
    return filename


def extract_content(skill_dir: str):
    CONTENT_DIR = Path(skill_dir) / "content"
    response = {}
     # resource intro variants
    markers = [
        "Visit the following resources",
        "To learn more, visit the following links",
        "Learn more from the following resources"
    ]
    for filename in os.listdir(CONTENT_DIR):
        if filename.endswith(".md"):
            filepath = os.path.join(CONTENT_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            # --- Extract description (everything before "Visit the following resources") ---
            # --- Find earliest marker and split ---
            split_point = len(text)
            for marker in markers:
                idx = text.find(marker)
                if idx != -1 and idx < split_point:
                    split_point = idx
            description = text[:split_point].strip()

            # --- Extract resource links ---
            urls = []
            resources_text = text[split_point:]
            resource_pattern = r'- \[@(\w+)@([^\]]+)\]\(([^)]+)\)'
            matches = re.findall(resource_pattern, text)
            
            for match in matches:
                resource_type, title, url = match
                # Map resource types to our schema
                type_mapping = {
                    'official': 'course',
                    'article': 'article', 
                    'opensource': 'tutorial',
                    'video': 'video',
                    'guide': 'guide',
                    'course': 'course'
                }
                
                urls.append({
                    "type": type_mapping.get(resource_type, 'article'),
                    "title": title,
                    "url": url
                })
            response[get_content_key(filename)] = {
                "description": description,
                "resources": urls
            }
    return response


def create_nodes_and_edges(roadmap: dict):
    roadmap_keys = list(roadmap.keys())
    response = {'nodes': [], 'edges': []}
    for i in range(len(roadmap_keys)):
        main_topic = roadmap[roadmap_keys[i]]
        # print(main_topic)
        response["nodes"].append({
            "id": main_topic["id"],
            "name": main_topic["name"],
            "resources": main_topic["resources"]
        })
        # Add edges to next main topic (if exists)
        if i < len(roadmap_keys) - 1:
            next_topic = roadmap[roadmap_keys[i + 1]]
            response["edges"].append({
                "source": main_topic["id"],
                "target": next_topic["id"]
            })
        for subtopic in main_topic["subtopics"]:
            # print(subtopic)
            response["nodes"].append({
                "id": subtopic["id"],
                "name": subtopic["name"],
                "resources": subtopic["resources"]
            })
            response["edges"].append({
                "source": main_topic["id"],
                "target": subtopic["id"]
            })
    return response


def generate_mapping_based_roadmap(mapping: dict, content: dict):
    roadmap = {}
    for mapping_key in mapping.keys():
        topics = mapping_key.split(":")
        main_topic = topics[0]
        if main_topic not in roadmap:
            resources = content.get(mapping[mapping_key], {})
            roadmap[main_topic] = {
                "id": mapping[mapping_key],
                "name": main_topic,
                "resources": resources,
                "subtopics": []
            }
        if len(topics) > 1:
            resources = content.get(mapping[mapping_key], {})
            roadmap[main_topic]["subtopics"].append({
                "id": mapping[mapping_key],
                "name": topics[1],
                "resources": resources
            })
    final_roadmap = create_nodes_and_edges(roadmap)
    return final_roadmap


def generate_json_based_roadmap(data: dict, content: dict):
    roadmap = {'nodes': [], 'edges': []}
    for node in data["nodes"]:
        if node["type"] in ["topic", "subtopic"]: # "paragraph"
            node_name = node["data"]["label"]
            resources = content.get(node["id"], {})
            roadmap["nodes"].append({
                "id": node["id"],
                "name": node_name,
                "resources": resources
            })
    for edge in data["edges"]:
        # print(edge)
        roadmap["edges"].append({
            "source": edge.get("source", ""),
            "target": edge.get("target", "")
        })
    return roadmap


def create_roadmap(skill_location: str, content: dict):
    skill_dir = Path(skill_location)
    skill_name = skill_dir.name

    # migration_mapping_file = skill_dir / "migration-mapping.json"
    # if migration_mapping_file.exists():
    #     with open(migration_mapping_file, 'r', encoding='utf-8') as f:
    #         data = json.load(f)
    #         return generate_mapping_based_roadmap(data, content), True
    
    main_json_file = skill_dir / f"{skill_name}.json"
    if main_json_file.exists():
        with open(main_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "nodes" in data and "edges" in data:
                return generate_json_based_roadmap(data, content), True
    return {}, False


def get_roadmap_and_content(skill_location: str):
    skill_name = skill_location.split("/")[-1]
    content = extract_content(skill_location)
    # print(content)
    # with open("data/" + skill_name + "_parsed_content.json", "w", encoding="utf-8") as f:
    #     json.dump(content, f, indent=2, ensure_ascii=False)
    roadmap = create_roadmap(skill_location, content)
    with open("data/" + skill_name + "_roadmap.json", "w", encoding="utf-8") as f:
        json.dump(roadmap[0], f, indent=2, ensure_ascii=False)
    

base_path = "raw_data"

for folder_name in os.listdir(base_path):
    folder_path = os.path.join(base_path, folder_name)
    if os.path.isdir(folder_path):
        print(folder_name)
        get_roadmap_and_content(base_path + "/" + folder_name)
