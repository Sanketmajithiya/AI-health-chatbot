import streamlit as st

# 🔄 Show spinner while loading model and retriever
with st.spinner("🔄 Please wait, loading AI model and medical data..."):
    from chatbot import get_bot_response  # ✅ Slow import wrapped in spinner

# Page setup
st.set_page_config(page_title="Sanket Chatbot", page_icon="🩺")

# ✅ Inject CSS and Footer FIRST (before anything else)
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
    </style>

    <div class="footer">
        Designed with ❤️ by <span>Sanket Majithiya</span>
    </div>
    """,
    unsafe_allow_html=True
)

# Title
st.title("🩺 Medical Chatbot")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input field
user_input = st.chat_input("Ask any medical question...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = get_bot_response(user_input)
            st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
