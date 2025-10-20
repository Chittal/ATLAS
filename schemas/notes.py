from pydantic import BaseModel
from typing import List, Optional

# Pydantic models for request/response
class NoteCreate(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = []
    is_favorite: Optional[bool] = False

class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None

class NoteResponse(BaseModel):
    id: str
    title: str
    content: str
    tags: List[str]
    is_favorite: bool
    created: str
    updated: str