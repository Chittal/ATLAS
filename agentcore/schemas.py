"""
Schemas for the agent
"""
from typing import Dict, List, Any, Optional, TypedDict
from langchain_core.runnables import RunnableConfig

class AgentState(TypedDict):
    """State for the agent execution"""
    current_message: str
    messages: List[Dict[str, str]]
    status: str
    step: str
    is_complete: bool
    metadata: Dict[str, Any]
    category: Optional[str]
    start_skill: Optional[str]
    target_skill: Optional[str]
    path_objects: List[Dict[str, Any]]
    error: Optional[str]

class SkillInfo(TypedDict):
    """Information about a skill"""
    id: str
    name: str
    description: Optional[str]
    order_index: int

class SkillConnection(TypedDict):
    """Connection between skills"""
    from_skill: str
    to_skill: str
    relationship_type: str
    weight: int

class LearningPathNode(TypedDict):
    """Node in a learning path"""
    id: str
    name: str

class LearningPath(TypedDict):
    """Learning path between skills"""
    start_skill: str
    target_skill: str
    path: List[LearningPathNode]
    total_steps: int

class PrerequisiteInfo(TypedDict):
    """Prerequisite information"""
    id: str
    name: str

class AgentRequest(TypedDict):
    """Request to the agent"""
    message: str
    user_id: Optional[str]
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]]

class AgentResponse(TypedDict):
    """Response from the agent"""
    message: str
    status: str
    category: str
    path_objects: Optional[List[Dict[str, Any]]]
    error: Optional[str]
    metadata: Dict[str, Any]
