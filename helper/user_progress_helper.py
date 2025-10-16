import hashlib
from typing import List, Dict, Optional
from config import app_config


class UserProgressHelper:
    """Helper class for managing user progress tracking with PocketBase"""
    
    def __init__(self, pb_instance):
        # Require an explicit PocketBase instance (admin client recommended)
        self.pb = pb_instance
        self.secret = app_config.secret
        
        if not self.pb:
            raise RuntimeError("PocketBase client not provided to UserProgressHelper")
        if not self.secret:
            raise RuntimeError("SECRET not configured in environment variables")
        
        # Quick smoke test
        try:
            _ = self.pb.collection('roadmaps').get_list(1, 1)
        except Exception as e:
            raise RuntimeError(f"PocketBase client invalid or unauthorized: {e}")
    
    def _generate_skill_sequence_hash(self, skill_sequence: str) -> str:
        """Generate a hash for skill sequence using SECRET"""
        if not self.secret:
            raise ValueError("SECRET not configured in environment variables")
        
        # Combine secret with skill sequence and hash
        combined = f"{self.secret}{skill_sequence}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]  # Short hash
    
    def _create_roadmap_name(self, start_skill: str, target_skill: str) -> str:
        """Create roadmap name in format: start skill-target-skill"""
        return f"{start_skill}-{target_skill}"
    
    def save_user_roadmap_path(self, user_id: str, start_skill: str, target_skill: str, 
                              skill_path: List[Dict]) -> Dict:
        """Persist user's roadmap path and mappings in PocketBase (admin client)."""
        roadmap_name = self._create_roadmap_name(start_skill, target_skill)
        skill_sequence = "-".join([skill["name"] for skill in skill_path])
        skill_sequence_hash = self._generate_skill_sequence_hash(skill_sequence)

        # 1) Roadmap (by name)
        existing_roadmaps = self.pb.collection('roadmaps').get_list(1, 1, {
            "filter": f"name = '{roadmap_name}'"
        })
        if existing_roadmaps.items:
            roadmap_id = existing_roadmaps.items[0].id
        else:
            roadmap = self.pb.collection('roadmaps').create({
                "name": roadmap_name,
                "description": f"Learning path from {start_skill} to {target_skill}"
            })
            roadmap_id = roadmap.id

        # 2) Roadmap path (by skill_sequence_hash)
        existing_paths = self.pb.collection('roadmap_paths').get_list(1, 1, {
            "filter": f"skill_sequence_hash = '{skill_sequence_hash}'"
        })
        if existing_paths.items:
            roadmap_path_id = existing_paths.items[0].id
        else:
            roadmap_path = self.pb.collection('roadmap_paths').create({
                "name": f"Path: {skill_sequence}",
                "roadmap_id": roadmap_id,
                "skill_sequence_hash": skill_sequence_hash,
                "description": f"Learning path: {skill_sequence}"
            })
            roadmap_path_id = roadmap_path.id

            # 3) Path skills
            for index, skill in enumerate(skill_path):
                self.pb.collection('roadmap_path_skills').create({
                    "roadmap_path_id": roadmap_path_id,
                    "skill_id": skill["id"],
                    "order_index": index,
                    "learning_nodes_count": skill.get("learning_nodes_count", 0)
                })

        # 4) User mapping
        existing_user_paths = self.pb.collection('user_roadmap_path').get_list(1, 1, {
            "filter": f"user_id = '{user_id}' && roadmap_path_id = '{roadmap_path_id}'"
        })
        if not existing_user_paths.items:
            user_roadmap_path = self.pb.collection('user_roadmap_path').create({
                "user_id": user_id,
                "roadmap_path_id": roadmap_path_id,
                "progress": 0.0
            })
            user_roadmap_path_id = user_roadmap_path.id
        else:
            user_roadmap_path_id = existing_user_paths.items[0].id

        return {
            "success": True,
            "roadmap_id": roadmap_id,
            "roadmap_path_id": roadmap_path_id,
            "user_roadmap_path_id": user_roadmap_path_id,
            "skill_sequence": skill_sequence,
            "skill_sequence_hash": skill_sequence_hash
        }
    
    def get_user_roadmap_paths(self, user_id: str) -> List[Dict]:
        """Get all roadmap paths for a user (admin client)."""
        user_paths = self.pb.collection('user_roadmap_path').get_list(1, 50, {
            "filter": f"user_id = '{user_id}'",
            "expand": "roadmap_path_id,roadmap_path_id.roadmap_id"
        })
        return [{
            "id": path.id,
            "progress": getattr(path, 'progress', 0),
            "completed_at": getattr(path, 'completed_at', None),
            "roadmap_path_id": getattr(path, 'roadmap_path_id', None),
            "created": getattr(path, 'created', None),
            "updated": getattr(path, 'updated', None)
        } for path in user_paths.items]
    
    def update_user_progress(self, user_roadmap_path_id: str, progress: float, 
                           completed_at: Optional[str] = None) -> Dict:
        """Update user's progress on a roadmap path (admin client)."""
        update_data = {"progress": progress}
        if completed_at:
            update_data["completed_at"] = completed_at
        updated_path = self.pb.collection('user_roadmap_path').update(
            user_roadmap_path_id, 
            update_data
        )
        return {
            "success": True,
            "progress": getattr(updated_path, 'progress', progress),
            "completed_at": getattr(updated_path, 'completed_at', completed_at)
        }
    
    def save_learning_node_completion(self, user_id: str, learning_node_id: str, 
                                    skill_id: str, user_roadmap_path_id: str, 
                                    completed_at: str = None) -> Dict:
        """Save learning node completion to user_learning_node_progress table."""
        if not completed_at:
            from datetime import datetime
            completed_at = datetime.utcnow().isoformat() + "Z"
        
        # Check if already completed
        existing_progress = self.pb.collection('user_learning_node_progress').get_list(1, 1, {
            "filter": f"learning_node_id = '{learning_node_id}' && user_roadmap_path_id = '{user_roadmap_path_id}'"
        })
        
        if existing_progress.items:
            # Update existing record
            updated_progress = self.pb.collection('user_learning_node_progress').update(
                existing_progress.items[0].id,
                {"completed_at": completed_at}
            )
            return {
                "success": True,
                "action": "updated",
                "progress_id": updated_progress.id,
                "completed_at": completed_at
            }
        else:
            # Create new record
            new_progress = self.pb.collection('user_learning_node_progress').create({
                "user_roadmap_path_id": user_roadmap_path_id,
                "learning_node_id": learning_node_id,
                "skill_id": skill_id,
                "completed_at": completed_at
            })
            return {
                "success": True,
                "action": "created",
                "progress_id": new_progress.id,
                "completed_at": completed_at
            }
    
    def get_user_learning_node_progress(self, user_id: str, user_roadmap_path_id: str = None) -> List[Dict]:
        """Get user's learning node progress."""
        filter_conditions = [f"user_roadmap_path_id.user_id = '{user_id}'"]
        if user_roadmap_path_id:
            filter_conditions.append(f"user_roadmap_path_id = '{user_roadmap_path_id}'")
        
        progress_records = self.pb.collection('user_learning_node_progress').get_list(1, 100, {
            "filter": " && ".join(filter_conditions),
            "expand": "user_roadmap_path_id"
        })
        
        return [{
            "id": record.id,
            "learning_node_id": getattr(record, 'learning_node_id', ''),
            "skill_id": getattr(record, 'skill_id', ''),
            "user_roadmap_path_id": getattr(record, 'user_roadmap_path_id', ''),
            "completed_at": getattr(record, 'completed_at', None),
            "created": getattr(record, 'created', None),
            "updated": getattr(record, 'updated', None)
        } for record in progress_records.items]
    
    def remove_learning_node_completion(self, user_id: str, learning_node_id: str, 
                                      user_roadmap_path_id: str) -> Dict:
        """Remove learning node completion (mark as incomplete)."""
        existing_progress = self.pb.collection('user_learning_node_progress').get_list(1, 1, {
            "filter": f"learning_node_id = '{learning_node_id}' && user_roadmap_path_id = '{user_roadmap_path_id}'"
        })
        
        if existing_progress.items:
            self.pb.collection('user_learning_node_progress').delete(existing_progress.items[0].id)
            return {
                "success": True,
                "action": "removed",
                "learning_node_id": learning_node_id
            }
        else:
            return {
                "success": True,
                "action": "not_found",
                "learning_node_id": learning_node_id
            }
    
    def update_learning_nodes_count(self, skill_name: str, learning_nodes_count: int) -> Dict:
        """Update learning_nodes_count in roadmap_path_skills table for a specific skill."""
        try:
            # Find all roadmap_path_skills records for this skill
            # Note: We need to find by skill name since we don't have the skill ID directly
            # This assumes skill_name matches the skill_id in the database
            skill_records = self.pb.collection('roadmap_path_skills').get_list(1, 100, {
                "filter": f"skill_id = '{skill_name}'"
            })
            print(f"Skill records: {skill_records}")
            updated_count = 0
            for record in skill_records.items:
                # Only update if the count is different (avoid unnecessary updates)
                current_count = getattr(record, 'learning_nodes_count', 0)
                if current_count != learning_nodes_count:
                    self.pb.collection('roadmap_path_skills').update(record.id, {
                        "learning_nodes_count": learning_nodes_count
                    })
                    updated_count += 1
            
            return {
                "success": True,
                "skill_name": skill_name,
                "learning_nodes_count": learning_nodes_count,
                "records_updated": updated_count,
                "total_records_found": len(skill_records.items)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "skill_name": skill_name,
                "learning_nodes_count": learning_nodes_count
            }

    def update_learning_nodes_count_by_ids(self, roadmap_path_id: str, skill_id: str, learning_nodes_count: int) -> Dict:
        """Update learning_nodes_count in roadmap_path_skills filtered by both roadmap_path_id and skill_id."""
        try:
            records = self.pb.collection('roadmap_path_skills').get_list(1, 5, {
                "filter": f"roadmap_path_id = '{roadmap_path_id}' && skill_id = '{skill_id}'"
            })
            print(f"Records: {records}")
            if not records.items:
                return {"success": False, "error": "record_not_found", "roadmap_path_id": roadmap_path_id, "skill_id": skill_id}

            print(f"Record: {records.items[0]}")
            record = records.items[0]
            current_count = getattr(record, 'learning_nodes_count', 0)
            if current_count == learning_nodes_count:
                return {"success": True, "records_updated": 0, "learning_nodes_count": learning_nodes_count}

            self.pb.collection('roadmap_path_skills').update(record.id, {
                "learning_nodes_count": learning_nodes_count
            })
            print(f"Record updated: {record}")
            return {"success": True, "records_updated": 1, "learning_nodes_count": learning_nodes_count}
        except Exception as e:
            return {"success": False, "error": str(e), "roadmap_path_id": roadmap_path_id, "skill_id": skill_id}
