from typing import TypedDict

class State(TypedDict):
    graph_id: str
    graph_status: str
    rejection_feedback: list[dict]
