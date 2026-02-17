"""
Chat Session Manager for Medical Chatbot
Handles multiple chat sessions with persistence
"""
import json
import os
from datetime import datetime
from typing import List, Dict

CHATS_DIR = "saved_chats"

def ensure_chats_directory():
    """Create chats directory if it doesn't exist"""
    if not os.path.exists(CHATS_DIR):
        os.makedirs(CHATS_DIR)

def get_chat_title(messages: List[Dict]) -> str:
    """Generate chat title from first user message"""
    for msg in messages:
        if msg.get("role") == "user":
            content = msg.get("content", "")
            # Take first 50 chars
            return content[:50] + "..." if len(content) > 50 else content
    return "New Chat"

def save_chat(chat_id: str, messages: List[Dict], title: str = None, pinned: bool = None, archived: bool = None):
    """Save chat session to file"""
    ensure_chats_directory()
    
    if not title and messages:
        title = get_chat_title(messages)
    elif not title:
        title = "New Chat"
    
    # Load existing data to preserve status ONLY if not explicitly provided
    existing_chat = load_chat(chat_id)
    
    if pinned is None and existing_chat:
        pinned = existing_chat.get("pinned", False)
    elif pinned is None:
        pinned = False
    
    if archived is None and existing_chat:
        archived = existing_chat.get("archived", False)
    elif archived is None:
        archived = False
    
    chat_data = {
        "id": chat_id,
        "title": title,
        "messages": messages,
        "pinned": pinned,
        "archived": archived,
        "created_at": existing_chat.get("created_at") if existing_chat else datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    filepath = os.path.join(CHATS_DIR, f"{chat_id}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(chat_data, f, indent=2, ensure_ascii=False)

def load_chat(chat_id: str) -> Dict:
    """Load chat session from file"""
    filepath = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def list_chats(search_query: str = None, show_archived: bool = False) -> List[Dict]:
    """List all saved chats with optional search and archive filter"""
    ensure_chats_directory()
    chats = []
    
    for filename in os.listdir(CHATS_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(CHATS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                    
                    # Archive filter
                    is_archived = chat_data.get("archived", False)
                    if show_archived and not is_archived:
                        continue  # Skip non-archived when showing archived
                    if not show_archived and is_archived:
                        continue  # Skip archived when showing normal chats
                    
                    # Search filter
                    if search_query:
                        title = chat_data.get("title", "").lower()
                        # Search in messages too
                        messages_text = " ".join([msg.get("content", "").lower() 
                                                 for msg in chat_data.get("messages", [])])
                        
                        if search_query.lower() not in title and search_query.lower() not in messages_text:
                            continue
                    
                    chats.append({
                        "id": chat_data.get("id"),
                        "title": chat_data.get("title", "Untitled"),
                        "pinned": chat_data.get("pinned", False),
                        "archived": chat_data.get("archived", False),
                        "updated_at": chat_data.get("updated_at"),
                        "message_count": len(chat_data.get("messages", []))
                    })
            except:
                continue
    
    # Sort: pinned first, then by updated_at
    chats.sort(key=lambda x: (not x.get("pinned", False), x.get("updated_at", "")), reverse=True)
    return chats

def delete_chat(chat_id: str):
    """Delete a chat session"""
    filepath = os.path.join(CHATS_DIR, f"{chat_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False

def rename_chat(chat_id: str, new_title: str):
    """Rename a chat session"""
    chat_data = load_chat(chat_id)
    if chat_data:
        chat_data["title"] = new_title
        chat_data["updated_at"] = datetime.now().isoformat()
        save_chat(chat_id, chat_data["messages"], new_title, 
                 chat_data.get("pinned", False), chat_data.get("archived", False))
        return True
    return False

def toggle_pin(chat_id: str) -> bool:
    """Toggle pin status of a chat"""
    chat_data = load_chat(chat_id)
    if chat_data:
        current_pinned = chat_data.get("pinned", False)
        save_chat(chat_id, chat_data["messages"], chat_data["title"], 
                 not current_pinned, chat_data.get("archived", False))
        return not current_pinned
    return False

def toggle_archive(chat_id: str) -> bool:
    """Toggle archive status of a chat"""
    chat_data = load_chat(chat_id)
    if chat_data:
        current_archived = chat_data.get("archived", False)
        # Unpin if archiving
        pinned = False if not current_archived else chat_data.get("pinned", False)
        save_chat(chat_id, chat_data["messages"], chat_data["title"], 
                 pinned, not current_archived)
        return not current_archived
    return False

def generate_chat_id() -> str:
    """Generate unique chat ID"""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")
