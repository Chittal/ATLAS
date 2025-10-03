from typing import TypedDict, Optional

class State(TypedDict):
    graph_id: str
    graph_status: str
    rejection_feedback: list[dict]


class AgentState(TypedDict):
    is_complete: bool = False
    metadata: dict
    current_message: str = None
    error: Optional[str] = None
    status: str = "start"
    step: str = "classify_query"
    category: str = None
    messages: list[dict] = []