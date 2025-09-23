#!/usr/bin/env python3
"""
Dual extraction script for learning roadmap data with two different JSON formats.

This script handles two different types of learning map structures:

1. **Migration-based format** (like Docker):
   - Uses migration-mapping.json + content/*.md files
   - Structure: {topic-name: file-id} mapping

2. **Direct JSON format** (like AI Agents):
   - Uses direct JSON with nodes and edges
   - Structure: {"nodes": [...], "edges": [...]} with visual layout data

Both are converted to the tracks_mapping_schema.json format.

Usage:
    python extract_roadmap_dual.py --skill docker --format migration
    python extract_roadmap_dual.py --skill ai-agents --format direct
    python extract_roadmap_dual.py --all  # Auto-detect format for all skills
"""

import json
import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

class MigrationBasedExtractor:
    """Extractor for migration-mapping.json based learning maps (like Docker)."""
    
    def __init__(self, skill_dir: str):
        self.skill_dir = Path(skill_dir)
        self.skill_name = self.skill_dir.name
        self.content_dir = self.skill_dir / "content"
        self.mapping_file = self.skill_dir / "migration-mapping.json"
        
        if not self.skill_dir.exists():
            raise ValueError(f"Skill directory '{skill_dir}' does not exist")
        
        if not self.mapping_file.exists():
            raise ValueError(f"Migration mapping file not found in '{skill_dir}'")
        
        # Load the migration mapping
        with open(self.mapping_file, 'r', encoding='utf-8') as f:
            self.migration_mapping = json.load(f)
        
        # Auto-generate learning path structure from the mapping
        self.learning_path = self._generate_learning_path()

    def _generate_learning_path(self) -> Dict[str, Dict[str, List[str]]]:
        """Auto-generate learning path structure from migration mapping."""
        learning_path = {}
        
        for topic_key in self.migration_mapping.keys():
            if ':' in topic_key:
                # This is a subtopic
                main_topic, subtopic = topic_key.split(':', 1)
                if main_topic not in learning_path:
                    learning_path[main_topic] = {"subtopics": []}
                learning_path[main_topic]["subtopics"].append(subtopic)
            else:
                # This is a main topic
                if topic_key not in learning_path:
                    learning_path[topic_key] = {"subtopics": []}
        
        return learning_path

    def extract_resources_from_content(self, content: str) -> List[Dict[str, str]]:
        """Extract resources from markdown content."""
        resources = []
        
        # Look for resource links in the format: - [@type@Title](URL)
        resource_pattern = r'- \[@(\w+)@([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(resource_pattern, content)
        
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
            
            resources.append({
                "type": type_mapping.get(resource_type, 'article'),
                "title": title,
                "url": url,
                "difficulty": "intermediate"  # Default difficulty
            })
        
        return resources

    def get_content_for_topic(self, topic_key: str) -> Optional[str]:
        """Get content for a topic from the migration mapping."""
        if topic_key in self.migration_mapping:
            content_file_id = self.migration_mapping[topic_key]
            content_file = self.content_dir / f"{topic_key}@{content_file_id}.md"
            
            if content_file.exists():
                with open(content_file, 'r', encoding='utf-8') as f:
                    return f.read()
        return None

    def generate_node_id(self, topic_name: str) -> str:
        """Generate a consistent node ID from topic name."""
        return topic_name.replace('-', '').replace('_', '')

    def extract_description(self, content: str) -> str:
        """Extract description from markdown content."""
        if not content:
            return ""
        
        # Get the first paragraph after the title
        lines = content.split('\n')
        description_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-') and not line.startswith('Visit the following'):
                description_lines.append(line)
                if len(description_lines) >= 2:  # Take first 2 paragraphs
                    break
        
        return ' '.join(description_lines)[:200] + "..." if len(' '.join(description_lines)) > 200 else ' '.join(description_lines)

    def create_nodes(self) -> List[Dict[str, Any]]:
        """Create nodes from the learning path."""
        nodes = []
        
        for main_topic, topic_data in self.learning_path.items():
            # Create main topic node
            main_topic_content = self.get_content_for_topic(main_topic)
            main_resources = self.extract_resources_from_content(main_topic_content) if main_topic_content else []
            
            main_node = {
                "id": self.generate_node_id(main_topic),
                "name": main_topic.replace('-', ' ').title(),
                "description": self.extract_description(main_topic_content) if main_topic_content else f"Learn about {main_topic.replace('-', ' ')}",
                "resources": {
                    "technical_workers": {"resources": main_resources},
                    "knowledge_workers": {"resources": main_resources},
                    "managers": {"resources": main_resources}
                }
            }
            nodes.append(main_node)
            
            # Create subtopic nodes
            for subtopic in topic_data["subtopics"]:
                subtopic_key = f"{main_topic}:{subtopic}"
                subtopic_content = self.get_content_for_topic(subtopic_key)
                subtopic_resources = self.extract_resources_from_content(subtopic_content) if subtopic_content else []
                
                subtopic_node = {
                    "id": self.generate_node_id(subtopic_key),
                    "name": subtopic.replace('-', ' ').title(),
                    "parent_id": self.generate_node_id(main_topic),
                    "description": self.extract_description(subtopic_content) if subtopic_content else f"Learn about {subtopic.replace('-', ' ')}",
                    "resources": {
                        "technical_workers": {"resources": subtopic_resources},
                        "knowledge_workers": {"resources": subtopic_resources},
                        "managers": {"resources": subtopic_resources}
                    }
                }
                nodes.append(subtopic_node)
        
        return nodes

    def create_edges(self) -> List[Dict[str, str]]:
        """Create edges based on the learning path structure."""
        edges = []
        
        # Define the learning progression
        main_topics = list(self.learning_path.keys())
        
        # Create sequential edges between main topics
        for i in range(len(main_topics) - 1):
            from_topic = self.generate_node_id(main_topics[i])
            to_topic = self.generate_node_id(main_topics[i + 1])
            
            # Add edges for all audience types
            for audience in ["technical_workers", "knowledge_workers", "managers"]:
                edges.append({
                    "from": from_topic,
                    "to": to_topic,
                    "audience_type": audience
                })
        
        # Create edges from main topics to their subtopics
        for main_topic, topic_data in self.learning_path.items():
            main_topic_id = self.generate_node_id(main_topic)
            
            for subtopic in topic_data["subtopics"]:
                subtopic_id = self.generate_node_id(f"{main_topic}:{subtopic}")
                
                # Add edges for all audience types
                for audience in ["technical_workers", "knowledge_workers", "managers"]:
                    edges.append({
                        "from": main_topic_id,
                        "to": subtopic_id,
                        "audience_type": audience
                    })
        
        return edges

    def extract_to_schema(self) -> Dict[str, Any]:
        """Extract roadmap data to tracks_mapping_schema.json format."""
        return {
            "nodes": self.create_nodes(),
            "edges": self.create_edges()
        }


class DirectJsonExtractor:
    """Extractor for direct JSON format learning maps (like AI Agents)."""
    
    def __init__(self, skill_dir: str):
        self.skill_dir = Path(skill_dir)
        self.skill_name = self.skill_dir.name
        
        # Look for JSON files in the skill directory
        json_files = list(self.skill_dir.glob("*.json"))
        if not json_files:
            raise ValueError(f"No JSON files found in '{skill_dir}'")
        
        # Use the main JSON file (usually named after the skill)
        main_json_file = self.skill_dir / f"{self.skill_name}.json"
        if main_json_file.exists():
            self.json_file = main_json_file
        else:
            # Use the first JSON file that's not migration-mapping
            for json_file in json_files:
                if json_file.name != "migration-mapping.json":
                    self.json_file = json_file
                    break
            else:
                raise ValueError(f"No suitable JSON file found in '{skill_dir}'")
        
        # Load the JSON data
        with open(self.json_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # Check if it has the expected structure
        if "nodes" not in self.data or "edges" not in self.data:
            raise ValueError(f"JSON file '{self.json_file}' doesn't have expected 'nodes' and 'edges' structure")

    def extract_resources_from_content(self, content: str) -> List[Dict[str, str]]:
        """Extract resources from markdown content."""
        resources = []
        
        # Look for resource links in the format: - [@type@Title](URL)
        resource_pattern = r'- \[@(\w+)@([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(resource_pattern, content)
        
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
            
            resources.append({
                "type": type_mapping.get(resource_type, 'article'),
                "title": title,
                "url": url,
                "difficulty": "intermediate"  # Default difficulty
            })
        
        return resources

    def get_content_for_node(self, node_id: str) -> Optional[str]:
        """Get content for a node from the content directory."""
        content_dir = self.skill_dir / "content"
        if not content_dir.exists():
            return None
        
        # Look for content files that might match this node ID
        for content_file in content_dir.glob("*.md"):
            if node_id in content_file.name:
                with open(content_file, 'r', encoding='utf-8') as f:
                    return f.read()
        
        return None

    def extract_description(self, content: str) -> str:
        """Extract description from markdown content."""
        if not content:
            return ""
        
        # Get the first paragraph after the title
        lines = content.split('\n')
        description_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-') and not line.startswith('Visit the following'):
                description_lines.append(line)
                if len(description_lines) >= 2:  # Take first 2 paragraphs
                    break
        
        return ' '.join(description_lines)[:200] + "..." if len(' '.join(description_lines)) > 200 else ' '.join(description_lines)

    def create_nodes(self) -> List[Dict[str, Any]]:
        """Create nodes from the JSON data."""
        nodes = []
        
        for node in self.data["nodes"]:
            # Only process topic and subtopic nodes
            if node.get("type") not in ["topic", "subtopic"]:
                continue
            
            node_id = node["id"]
            node_data = node.get("data", {})
            label = node_data.get("label", f"Topic {node_id}")
            
            # Get content for this node
            content = self.get_content_for_node(node_id)
            resources = self.extract_resources_from_content(content) if content else []
            
            # Determine if this is a subtopic (has parent)
            parent_id = None
            if node.get("type") == "subtopic":
                # Try to find parent based on position or other heuristics
                # For now, we'll leave parent_id as None and let the edges define relationships
                pass
            
            node_obj = {
                "id": node_id,
                "name": label,
                "description": self.extract_description(content) if content else f"Learn about {label}",
                "resources": {
                    "technical_workers": {"resources": resources},
                    "knowledge_workers": {"resources": resources},
                    "managers": {"resources": resources}
                }
            }
            
            if parent_id:
                node_obj["parent_id"] = parent_id
            
            nodes.append(node_obj)
        
        return nodes

    def create_edges(self) -> List[Dict[str, str]]:
        """Create edges from the JSON data."""
        edges = []
        
        for edge in self.data["edges"]:
            source = edge.get("source")
            target = edge.get("target")
            
            if source and target:
                # Add edges for all audience types
                for audience in ["technical_workers", "knowledge_workers", "managers"]:
                    edges.append({
                        "from": source,
                        "to": target,
                        "audience_type": audience
                    })
        
        return edges

    def extract_to_schema(self) -> Dict[str, Any]:
        """Extract roadmap data to tracks_mapping_schema.json format."""
        return {
            "nodes": self.create_nodes(),
            "edges": self.create_edges()
        }


def detect_format(skill_dir: str) -> str:
    """Detect the format of a skill directory."""
    skill_path = Path(skill_dir)
    
    # Check for migration-mapping.json (migration-based format)
    if (skill_path / "migration-mapping.json").exists():
        return "migration"
    
    # Check for direct JSON format
    json_files = list(skill_path.glob("*.json"))
    for json_file in json_files:
        if json_file.name != "migration-mapping.json":
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "nodes" in data and "edges" in data:
                        return "direct"
            except:
                continue
    
    raise ValueError(f"Could not detect format for skill directory '{skill_dir}'")


def find_skill_directories(base_dir: str = ".") -> List[str]:
    """Find all skill directories."""
    base_path = Path(base_dir)
    skill_dirs = []
    
    for item in base_path.iterdir():
        if item.is_dir():
            # Check if it has either migration-mapping.json or JSON files
            if (item / "migration-mapping.json").exists() or list(item.glob("*.json")):
                skill_dirs.append(str(item))
    
    return skill_dirs


def main():
    """Main function to run the extraction."""
    parser = argparse.ArgumentParser(description="Extract learning roadmap data to tracks_mapping_schema.json format")
    parser.add_argument("--skill", help="Specific skill directory to extract (e.g., 'docker')")
    parser.add_argument("--format", choices=["migration", "direct", "auto"], default="auto", 
                       help="Format type: migration (migration-mapping.json), direct (JSON with nodes/edges), or auto-detect")
    parser.add_argument("--all", action="store_true", help="Extract all available skills")
    parser.add_argument("--output-dir", default=".", help="Output directory for generated files")
    
    args = parser.parse_args()
    
    if args.all:
        # Extract all available skills
        skill_dirs = find_skill_directories()
        if not skill_dirs:
            print("No skill directories found")
            return
        
        print(f"Found {len(skill_dirs)} skill directories: {[Path(d).name for d in skill_dirs]}")
        
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        
        for skill_dir in skill_dirs:
            try:
                # Auto-detect format
                format_type = detect_format(skill_dir)
                print(f"\nProcessing {Path(skill_dir).name} (format: {format_type})")
                
                if format_type == "migration":
                    extractor = MigrationBasedExtractor(skill_dir)
                else:
                    extractor = DirectJsonExtractor(skill_dir)
                
                output_file = output_dir / f"{extractor.skill_name}_roadmap.json"
                data = extractor.extract_to_schema()
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"{extractor.skill_name.title()} roadmap data extracted to {output_file}")
                print(f"Total nodes: {len(data['nodes'])}")
                print(f"Total edges: {len(data['edges'])}")
                
            except Exception as e:
                print(f"Error processing {skill_dir}: {e}")
                print()
    
    elif args.skill:
        # Extract specific skill
        try:
            # Determine format
            if args.format == "auto":
                format_type = detect_format(args.skill)
            else:
                format_type = args.format
            
            print(f"Processing {args.skill} (format: {format_type})")
            
            if format_type == "migration":
                extractor = MigrationBasedExtractor(args.skill)
            else:
                extractor = DirectJsonExtractor(args.skill)
            
            output_file = Path(args.output_dir) / f"{extractor.skill_name}_roadmap.json"
            data = extractor.extract_to_schema()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"{extractor.skill_name.title()} roadmap data extracted to {output_file}")
            print(f"Total nodes: {len(data['nodes'])}")
            print(f"Total edges: {len(data['edges'])}")
            
        except Exception as e:
            print(f"Error: {e}")
            return
    
    else:
        # Show available skills
        skill_dirs = find_skill_directories()
        if skill_dirs:
            print("Available skills:")
            for skill_dir in skill_dirs:
                try:
                    format_type = detect_format(skill_dir)
                    print(f"  - {Path(skill_dir).name} (format: {format_type})")
                except:
                    print(f"  - {Path(skill_dir).name} (format: unknown)")
            print("\nUse --skill <name> to extract a specific skill or --all to extract all skills")
        else:
            print("No skill directories found")


if __name__ == "__main__":
    main()
