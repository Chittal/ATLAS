from fastapi import Request, HTTPException, APIRouter
from fastapi.responses import RedirectResponse, HTMLResponse
from deps import templates, pb
from helper.helper import get_current_user
from typing import Optional
from schemas.notes import NoteCreate, NoteUpdate

router = APIRouter(
    prefix="",
    tags=["Notes"],
)

# Notes page route
@router.get("/notes", response_class=HTMLResponse)
async def notes_page(request: Request):
    """Notes page."""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    return templates.TemplateResponse("notes_content.html", {
        "request": request,
        "title": "Notes",
        "user": user
    })

# API Routes for Notes CRUD operations

@router.get("/api/user/notes")
async def get_user_notes(request: Request, search: Optional[str] = None, tag: Optional[str] = None, favorite: Optional[bool] = None):
    """Get all notes for the current user with optional filtering."""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Build filter conditions
        filter_conditions = [f"user_id = '{user.id}'"]
        
        if search:
            filter_conditions.append(f"(title ~ '{search}' || content ~ '{search}')")
        
        if tag:
            filter_conditions.append(f"tags ~ '{tag}'")
        
        if favorite is not None:
            filter_conditions.append(f"is_favorite = {str(favorite).lower()}")
        
        filter_string = " && ".join(filter_conditions)
        
        # Get notes from PocketBase
        from helper.pocketbase_helper import get_pb_admin_client
        admin_pb = get_pb_admin_client()
        notes = admin_pb.collection('notes').get_list(1, 100, {
            "filter": filter_string,
            "sort": "-updated"  # Sort by most recently updated first
        })
        
        # Convert to response format
        notes_list = []
        for note in notes.items:
            notes_list.append({
                "id": note.id,
                "title": getattr(note, 'title', ''),
                "content": getattr(note, 'content', ''),
                "tags": getattr(note, 'tags', []),
                "is_favorite": getattr(note, 'is_favorite', False),
                "created": getattr(note, 'created', ''),
                "updated": getattr(note, 'updated', '')
            })
        
        return {"success": True, "notes": notes_list}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting notes: {str(e)}")

@router.get("/api/user/notes/{note_id}")
async def get_note(request: Request, note_id: str):
    """Get a specific note by ID."""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Get note from PocketBase
        from helper.pocketbase_helper import get_pb_admin_client
        admin_pb = get_pb_admin_client()
        note = admin_pb.collection('notes').get_one(note_id)
        
        # Check if note belongs to user
        if getattr(note, 'user_id', '') != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return {
            "success": True,
            "note": {
                "id": note.id,
                "title": getattr(note, 'title', ''),
                "content": getattr(note, 'content', ''),
                "tags": getattr(note, 'tags', []),
                "is_favorite": getattr(note, 'is_favorite', False),
                "created": getattr(note, 'created', ''),
                "updated": getattr(note, 'updated', '')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting note: {str(e)}")

@router.post("/api/user/notes")
async def create_note(request: Request, note_data: NoteCreate):
    """Create a new note."""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Create note in PocketBase
        from helper.pocketbase_helper import get_pb_admin_client
        admin_pb = get_pb_admin_client()
        
        # Ensure tags are lowercase
        lowercase_tags = [tag.lower() for tag in note_data.tags] if note_data.tags else []
        
        note = admin_pb.collection('notes').create({
            "user_id": user.id,
            "title": note_data.title,
            "content": note_data.content,
            "tags": lowercase_tags,
            "is_favorite": note_data.is_favorite
        })
        
        return {
            "success": True,
            "message": "Note created successfully",
            "note": {
                "id": note.id,
                "title": getattr(note, 'title', ''),
                "content": getattr(note, 'content', ''),
                "tags": getattr(note, 'tags', []),
                "is_favorite": getattr(note, 'is_favorite', False),
                "created": getattr(note, 'created', ''),
                "updated": getattr(note, 'updated', '')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating note: {str(e)}")

@router.put("/api/user/notes/{note_id}")
async def update_note(request: Request, note_id: str, note_data: NoteUpdate):
    """Update an existing note."""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Check if note exists and belongs to user
        from helper.pocketbase_helper import get_pb_admin_client
        admin_pb = get_pb_admin_client()
        existing_note = admin_pb.collection('notes').get_one(note_id)
        if getattr(existing_note, 'user_id', '') != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Build update data (only include fields that are provided)
        update_data = {}
        if note_data.title is not None:
            update_data["title"] = note_data.title
        if note_data.content is not None:
            update_data["content"] = note_data.content
        if note_data.tags is not None:
            # Ensure tags are lowercase
            update_data["tags"] = [tag.lower() for tag in note_data.tags]
        if note_data.is_favorite is not None:
            update_data["is_favorite"] = note_data.is_favorite
        
        # Update note in PocketBase
        updated_note = admin_pb.collection('notes').update(note_id, update_data)
        
        return {
            "success": True,
            "message": "Note updated successfully",
            "note": {
                "id": updated_note.id,
                "title": getattr(updated_note, 'title', ''),
                "content": getattr(updated_note, 'content', ''),
                "tags": getattr(updated_note, 'tags', []),
                "is_favorite": getattr(updated_note, 'is_favorite', False),
                "created": getattr(updated_note, 'created', ''),
                "updated": getattr(updated_note, 'updated', '')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating note: {str(e)}")

@router.delete("/api/user/notes/{note_id}")
async def delete_note(request: Request, note_id: str):
    """Delete a note."""
    try:
        user = get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Check if note exists and belongs to user
        from helper.pocketbase_helper import get_pb_admin_client
        admin_pb = get_pb_admin_client()
        existing_note = admin_pb.collection('notes').get_one(note_id)
        if getattr(existing_note, 'user_id', '') != user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Delete note from PocketBase
        admin_pb.collection('notes').delete(note_id)
        
        return {
            "success": True,
            "message": "Note deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting note: {str(e)}")

@router.get("/api/user/tags")
async def get_user_tags(request: Request):
    """Get all unique tags used by the current user."""
    # try:
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get all notes for the user
    from helper.pocketbase_helper import get_pb_admin_client
    admin_pb = get_pb_admin_client()
    
    # Use a larger page size to get all notes, or implement pagination
    notes = admin_pb.collection('notes').get_list(1, 500, {
        "filter": f"user_id = '{user.id}'"
    })
    
    # Collect all unique tags
    all_tags = set()
    for note in notes.items:
        tags = getattr(note, 'tags', [])
        if isinstance(tags, list):
            all_tags.update(tags)
        elif isinstance(tags, str):
            # Handle case where tags might be stored as a string
            try:
                import json
                parsed_tags = json.loads(tags)
                if isinstance(parsed_tags, list):
                    all_tags.update(parsed_tags)
            except (json.JSONDecodeError, TypeError):
                # If it's not JSON, treat as a single tag
                if tags.strip():
                    all_tags.add(tags.strip())
    
    return {
        "success": True,
        "tags": sorted(list(all_tags))
    }
    
    # except HTTPException:
    #     raise
    # except Exception as e:
    #     print(f"Error getting tags: {e}")  # Debug logging
    #     raise HTTPException(status_code=500, detail=f"Error getting tags: {str(e)}")
