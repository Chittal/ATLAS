from typing import TypedDict, Optional


class AgentState(TypedDict):
    is_complete: bool = False
    metadata: dict
    current_message: str = None
    error: Optional[str] = None
    status: str = "start"
    step: str = "classify_query"
    category: str = None
    start_skill: str = None
    target_skill: str = None
    path_objects: list[dict] = []
    messages: list[dict] = []