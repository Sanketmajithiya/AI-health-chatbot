import streamlit as st
import os
from datetime import datetime
import chat_manager as cm

# 🔄 Show spinner while loading model and retriever
with st.spinner("🔄 Please wait, loading AI model and medical data..."):
    from chatbot import get_bot_response

# Page setup
st.set_page_config(page_title="Medical Chatbot", page_icon="🩺", layout="wide")

# ✅ Inject CSS and Footer
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        padding: 10px 0;
        text-align: center;
        font-size: 13px;
        font-family: 'Segoe UI', sans-serif;
        color: #888;
        background-color: transparent;
        z-index: 9999;
    }

    .footer span {
        color: #C084FC;
        font-weight: bold;
        text-shadow: 0px 0px 4px rgba(192,132,252,0.4);
    }
    
    .chat-item {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 6px;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    
    .chat-item:hover {
        background-color: rgba(255,255,255,0.1);
    }
    
    .chat-item-active {
        background-color: rgba(192,132,252,0.2);
        border-left: 3px solid #C084FC;
    }
    </style>

    <div class="footer">
        Designed with ❤️ by <span>Sanket Majithiya</span>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize session state
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = cm.generate_chat_id()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "auto_save" not in st.session_state:
    st.session_state.auto_save = True

# Sidebar - Chat History
with st.sidebar:
    st.header("💬 Your Chats")
    
    # New Chat Button
    if st.button("✨ New Chat", use_container_width=True, type="primary"):
        # Save current chat if has messages
        if st.session_state.messages:
            cm.save_chat(st.session_state.current_chat_id, st.session_state.messages)
        
        # Create new chat
        st.session_state.current_chat_id = cm.generate_chat_id()
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # Search Box
    search_query = st.text_input("🔍 Search chats", placeholder="Search by title or content...", key="chat_search")
    
    st.divider()
    
    # List saved chats with search
    saved_chats = cm.list_chats(search_query if search_query else None)
    
    if saved_chats:
        # Separate pinned and unpinned
        pinned_chats = [c for c in saved_chats if c.get("pinned", False)]
        unpinned_chats = [c for c in saved_chats if not c.get("pinned", False)]
        
        # Show pinned chats first
        if pinned_chats:
            st.subheader("📌 Pinned")
            for chat in pinned_chats:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Chat title button with pin indicator
                    button_label = f"📌 {chat['title']}"
                    if st.button(
                        button_label, 
                        key=f"chat_{chat['id']}", 
                        use_container_width=True,
                        type="secondary" if chat["id"] == st.session_state.current_chat_id else "tertiary"
                    ):
                        # Save current chat before switching
                        if st.session_state.messages:
                            cm.save_chat(st.session_state.current_chat_id, st.session_state.messages)
                        
                        # Load selected chat
                        loaded_chat = cm.load_chat(chat["id"])
                        if loaded_chat:
                            st.session_state.current_chat_id = chat["id"]
                            st.session_state.messages = loaded_chat.get("messages", [])
                            st.rerun()
                
                with col2:
                    # Chat options menu
                    with st.popover("⋮", use_container_width=True):
                        # Unpin option
                        if st.button("📍 Unpin", key=f"unpin_{chat['id']}", use_container_width=True):
                            cm.toggle_pin(chat["id"])
                            st.rerun()
                        
                        # Archive option
                        if st.button("🗄️ Archive", key=f"archive_{chat['id']}", use_container_width=True):
                            cm.toggle_archive(chat["id"])
                            st.rerun()
                        
                        if st.button("📝 Rename", key=f"rename_{chat['id']}", use_container_width=True):
                            st.session_state[f"renaming_{chat['id']}"] = True
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"del_{chat['id']}", use_container_width=True):
                            cm.delete_chat(chat["id"])
                            if chat["id"] == st.session_state.current_chat_id:
                                st.session_state.current_chat_id = cm.generate_chat_id()
                                st.session_state.messages = []
                            st.rerun()
                        
                        if st.button("💾 Export", key=f"exp_{chat['id']}", use_container_width=True):
                            loaded = cm.load_chat(chat["id"])
                            if loaded:
                                chat_text = f"# {loaded['title']}\n\n"
                                for msg in loaded.get("messages", []):
                                    role = "You" if msg["role"] == "user" else "Bot"
                                    chat_text += f"**{role}:** {msg['content']}\n\n"
                                
                                st.download_button(
                                    "📥 Download",
                                    data=chat_text,
                                    file_name=f"{chat['title'][:30]}.txt",
                                    mime="text/plain",
                                    key=f"dl_{chat['id']}"
                                )
                
                # Rename dialog
                if st.session_state.get(f"renaming_{chat['id']}", False):
                    new_title = st.text_input(
                        "New title:", 
                        value=chat["title"],
                        key=f"input_rename_{chat['id']}"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save", key=f"save_rename_{chat['id']}"):
                            cm.rename_chat(chat["id"], new_title)
                            st.session_state[f"renaming_{chat['id']}"] = False
                            st.rerun()
                    with col2:
                        if st.button("Cancel", key=f"cancel_rename_{chat['id']}"):
                            st.session_state[f"renaming_{chat['id']}"] = False
                            st.rerun()
            
            st.divider()
        
        # Show unpinned chats
        if unpinned_chats:
            st.subheader("Recent Chats")
            for chat in unpinned_chats:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Chat title button
                    if st.button(
                        chat["title"], 
                        key=f"chat_{chat['id']}", 
                        use_container_width=True,
                        type="secondary" if chat["id"] == st.session_state.current_chat_id else "tertiary"
                    ):
                        # Save current chat before switching
                        if st.session_state.messages:
                            cm.save_chat(st.session_state.current_chat_id, st.session_state.messages)
                        
                        # Load selected chat
                        loaded_chat = cm.load_chat(chat["id"])
                        if loaded_chat:
                            st.session_state.current_chat_id = chat["id"]
                            st.session_state.messages = loaded_chat.get("messages", [])
                            st.rerun()
                
                with col2:
                    # Chat options menu
                    with st.popover("⋮", use_container_width=True):
                        # Pin option
                        if st.button("📌 Pin", key=f"pin_{chat['id']}", use_container_width=True):
                            cm.toggle_pin(chat["id"])
                            st.rerun()
                        
                        # Archive option
                        if st.button("🗄️ Archive", key=f"archive_{chat['id']}", use_container_width=True):
                            cm.toggle_archive(chat["id"])
                            st.rerun()
                        
                        if st.button("📝 Rename", key=f"rename_{chat['id']}", use_container_width=True):
                            st.session_state[f"renaming_{chat['id']}"] = True
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"del_{chat['id']}", use_container_width=True):
                            cm.delete_chat(chat["id"])
                            if chat["id"] == st.session_state.current_chat_id:
                                st.session_state.current_chat_id = cm.generate_chat_id()
                                st.session_state.messages = []
                            st.rerun()
                        
                        if st.button("💾 Export", key=f"exp_{chat['id']}", use_container_width=True):
                            loaded = cm.load_chat(chat["id"])
                            if loaded:
                                chat_text = f"# {loaded['title']}\n\n"
                                for msg in loaded.get("messages", []):
                                    role = "You" if msg["role"] == "user" else "Bot"
                                    chat_text += f"**{role}:** {msg['content']}\n\n"
                                
                                st.download_button(
                                    "📥 Download",
                                    data=chat_text,
                                    file_name=f"{chat['title'][:30]}.txt",
                                    mime="text/plain",
                                    key=f"dl_{chat['id']}"
                                )
                
                # Rename dialog
                if st.session_state.get(f"renaming_{chat['id']}", False):
                    new_title = st.text_input(
                        "New title:", 
                        value=chat["title"],
                        key=f"input_rename_{chat['id']}"
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save", key=f"save_rename_{chat['id']}"):
                            cm.rename_chat(chat["id"], new_title)
                            st.session_state[f"renaming_{chat['id']}"] = False
                            st.rerun()
                    with col2:
                        if st.button("Cancel", key=f"cancel_rename_{chat['id']}"):
                            st.session_state[f"renaming_{chat['id']}"] = False
                            st.rerun()
    else:
        if search_query:
            st.info(f"No chats found for '{search_query}'")
        else:
            st.info("No saved chats yet. Start a conversation!")
    
    st.divider()
    
    # Archived Chats Section
    archived_chats = cm.list_chats(show_archived=True)
    
    if archived_chats:
        with st.expander(f"🗄️ Archived ({len(archived_chats)})", expanded=False):
            for chat in archived_chats:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    if st.button(
                        chat["title"], 
                        key=f"archived_{chat['id']}", 
                        use_container_width=True,
                        type="tertiary"
                   ):
                        # Load archived chat
                        loaded_chat = cm.load_chat(chat["id"])
                        if loaded_chat:
                            st.session_state.current_chat_id = chat["id"]
                            st.session_state.messages = loaded_chat.get("messages", [])
                            st.rerun()
                
                with col2:
                    with st.popover("⋮", use_container_width=True):
                        # Unarchive option
                        if st.button("📤 Unarchive", key=f"unarchive_{chat['id']}", use_container_width=True):
                            cm.toggle_archive(chat["id"])
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"del_arch_{chat['id']}", use_container_width=True):
                            cm.delete_chat(chat["id"])
                            st.rerun()
                        
                        if st.button("💾 Export", key=f"exp_arch_{chat['id']}", use_container_width=True):
                            loaded = cm.load_chat(chat["id"])
                            if loaded:
                                chat_text = f"# {loaded['title']}\n\n"
                                for msg in loaded.get("messages", []):
                                    role = "You" if msg["role"] == "user" else "Bot"
                                    chat_text += f"**{role}:** {msg['content']}\n\n"
                                
                                st.download_button(
                                    "📥 Download",
                                    data=chat_text,
                                    file_name=f"{chat['title'][:30]}.txt",
                                    mime="text/plain",
                                    key=f"dl_arch_{chat['id']}"
                                )
    
    st.divider()
    
    # Chat Stats  
    st.subheader("📊 Stats")
    msg_count = len(st.session_state.messages)
    total_chats = len(saved_chats) + len(archived_chats)
    st.metric("Messages", msg_count)
    st.metric("Active Chats", len(saved_chats))
    st.metric("Archived", len(archived_chats))
    
    st.divider()
    
    # Model Info
    st.subheader("🤖 Model")
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    st.info(f"**{model_name}**")
    st.caption("Groq (FREE)")
    
    st.divider()
    
    # Help Section
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        **What This Chatbot Does:**
        
        Get AI-powered medical information based on trusted medical literature. Ask about symptoms, conditions, treatments, and health topics.
        
        **3 Key Features:**
        
        1. **📌 Pin Important Chats**  
           Save frequently-used conversations at the top
        
        2. **🔍 Search All Chats**  
           Find past conversations by keywords
        
        3. **🗄️ Archive Old Chats**  
           Keep history organized & clutter-free
        
        ---
        
        ✅ **Powered by trusted medical literature and AI**  
        💡 **Use this for quick health insights and learning**
        """)

# Main chat area
st.title("🩺 Medical Chatbot")

# Welcome message
if len(st.session_state.messages) == 0:
    st.info("👋 Welcome! Ask me any medical question based on medical literature.")

# Show messages with delete option
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        col1, col2 = st.columns([20, 1])
        with col1:
            st.markdown(msg["content"])
        with col2:
            # Delete button for each message
            if st.button("🗑️", key=f"del_msg_{idx}", help="Delete this message"):
                st.session_state.messages.pop(idx)
                st.rerun()

# Input field
user_input = st.chat_input("Ask any medical question...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_bot_response(user_input)
            st.markdown(response)

    # Add assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Auto-save chat
    if st.session_state.auto_save:
        cm.save_chat(st.session_state.current_chat_id, st.session_state.messages)
    
    st.rerun()
