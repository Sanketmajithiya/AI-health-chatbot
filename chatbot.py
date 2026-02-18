from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from vector import load_retriever
import os
from dotenv import load_dotenv
import logging
import re
import datetime

load_dotenv()

# ===============================
# Logging Setup (Production Ready)
# ===============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===============================
# Global Lazy Load
# ===============================
_retriever = None
_model = None
_chain_patient = None
_chain_learning = None
_chain_casual = None

# ===============================
# Conversation Memory (User + Chat)
# ===============================
conversation_memory = []
MAX_MEMORY = 10
USER_NAME = "User" # Default name

def update_memory(user_input, bot_response):
    conversation_memory.append(f"User: {user_input}")
    conversation_memory.append(f"Bot: {bot_response}")

    while len(conversation_memory) > MAX_MEMORY:
        conversation_memory.pop(0)


def get_memory_context():
    return "\n".join(conversation_memory)

# ===============================
# NEW GLOBAL FLAG (NAME DETECT)
# ===============================
NAME_UPDATED = False


# ===============================
# Personalization (UPDATED)
# ===============================
def check_for_name_update(text):
    global USER_NAME, NAME_UPDATED

    text_lower = text.lower()

    patterns = [
        r"(?:call me|my name is|mera naam|mujhe) ([\w\s]+)(?:keh kar bulao|hai|bulao)?",
        r"(?:i am|main hoon) ([\w\s]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            potential_name = match.group(1).strip().title()

            if len(potential_name.split()) <= 3 and len(potential_name) > 1:
                USER_NAME = potential_name
                NAME_UPDATED = True
                return True

    return False

# ===============================
# Intent Detection (SAFE PRIORITY ROUTER)
# ===============================
CASUAL_KEYWORDS = [
    "hello","hi","hey","thanks","thank you","bye",
    "good morning","good evening","how are you",
    "who are you","your name","who made you"
]
GENERAL_KEYWORDS = [
    "date", "time", "day", "today", "tomorrow", "yesterday",
    "who is", "where is", "capital", "weather", "tell me",
    "joke", "quote", "fact"
]
DEFINITION_KEYWORDS = ["what is","define","meaning","explain","describe","full form"]
SYMPTOM_KEYWORDS = [
    "i have","pain","fever","vomiting","dizziness",
    "hurt","suffering","feeling","symptom","ache"
]

def detect_intent(text):
    text_lower = text.lower()

    # Name update is technically a "casual" interaction usually
    if check_for_name_update(text):
        return "casual" 

    # General Knowledge -> Casual Mode
    if any(w in text_lower for w in GENERAL_KEYWORDS):
        return "casual"

    # PRIORITY ORDER (IMPORTANT FOR SAFETY)
    if any(w in text_lower for w in SYMPTOM_KEYWORDS):
        return "patient"

    if any(w in text_lower for w in DEFINITION_KEYWORDS):
        return "learning"

    if any(w in text_lower for w in CASUAL_KEYWORDS) and len(text_lower.split()) <= 6:
        return "casual"

    if len(text_lower.split()) <= 3:
        return "casual"

    return "patient"

# ===============================
# Emergency Detection
# ===============================
EMERGENCY_KEYWORDS = [
    "chest pain","difficulty breathing","unconscious","seizure",
    "severe bleeding","stroke","heart attack","suicidal","can't breathe",
    "collapsed","poison","drug overdose"
]

def check_emergency(text):
    text_lower = text.lower()
    return any(word in text_lower for word in EMERGENCY_KEYWORDS)

# ===============================
# A.I. Triage System
# ===============================
def smart_triage(text):
    text_lower = text.lower()

    if any(w in text_lower for w in [
        "can't breathe","unconscious","severe bleeding",
        "heart attack","stroke","suicidal"
    ]):
        return "HIGH"

    if any(w in text_lower for w in [
        "fever","vomiting","persistent pain","dizziness","infection"
    ]):
        return "MODERATE"

    return "LOW"

def get_severity_level(level):
    if level == "HIGH":
        return "🚨 **Severity Level:** HIGH RISK - Seek immediate medical care."
    if level == "MODERATE":
        return "⚠️ **Severity Level:** MODERATE RISK - Consider consulting a doctor."
    return "✅ **Severity Level:** LOW RISK - Monitor symptoms."

# ===============================
# Retriever Loader (Crash Safe)
# ===============================
def get_retriever():
    global _retriever
    if _retriever is None:
        logger.info("Loading retriever...")
        _retriever = load_retriever()
    return _retriever

def safe_retrieve(query):
    try:
        retriever = get_retriever()
        docs = retriever.invoke(query) or []
        return "\n\n".join([doc.page_content for doc in docs[:4]])
    except Exception as e:
        logger.error(f"Retriever error: {e}")
        return "No relevant medical context found."

# ===============================
# Model & Prompt Loader
# ===============================
def get_model_and_chains():
    global _model, _chain_patient, _chain_learning, _chain_casual

    if _model is None:
        # Use a faster, lighter model to avoid Rate Limits (429) errors
        model_name = os.getenv("GROQ_MODEL") or "llama-3.1-8b-instant"
        temperature = float(os.getenv("TEMPERATURE") or "0.3")
        api_key = os.getenv("GROQ_API_KEY")

        _model = ChatGroq(
            model=model_name,
            temperature=temperature,
            groq_api_key=api_key
        )

        # CASUAL MODE (+ GENERAL KNOWLEDGE)
        casual_prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are 'MediBot', an intelligent and empathetic medical AI assistant.

- Address the user as '{user_name}'.
- Current Date & Time: {date_time}
- Handle greetings and GENERAL KNOWLEDGE questions (Date, Time, Basic Facts) naturally.
- Keep responses concise (1-3 sentences) but helpful.
- If asked who you are: "I am MediBot, your smart medical assistant."
- Avoid medical diagnosis here (redirect if needed).
- LANGUAGE: Detect the user's language and reply in the EXACT SAME language (English, Hindi, Hinglish, Spanish, etc.).
"""),
            ("human", "Conversation History:\n{history}\n\nUser:\n{question}")
        ])

        # PATIENT MODE
        patient_prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are a professional medical AI assistant.

IMPORTANT:
- Address the user as '{user_name}' if appropriate.
- Current Date: {date_time}
- Use retrieved context as PRIMARY source.
- Provide educational information only.
- Never give final diagnosis.
- LANGUAGE: ALL responses must be in the SAME LANGUAGE as the user's question. Translate the English medical context into the user's language naturally.

STRUCTURE:
🧠 Possible Explanation
📋 Common Symptoms
⚠️ Possible Causes
💊 General Care
🚨 When to Seek Medical Help
🤖 Follow-Up Questions (2 if needed)
"""),
            ("human", """
Conversation History:
{history}

Medical Context:
{context}

Patient Question:
{question}
""")
        ])

        # LEARNING MODE
        learning_prompt = ChatPromptTemplate.from_messages([
            ("system", """
You are a Medical Professor teaching '{user_name}'.

Explain clearly with:
- What
- Why
- How
Use simple language.
- LANGUAGE: Answer in the SAME LANGUAGE as the user. If they ask in Hindi/Hinglish, explain in Hindi/Hinglish.
"""),
            ("human", """
Context:
{context}

Student Question:
{question}
""")
        ])

        _chain_casual = casual_prompt | _model
        _chain_patient = patient_prompt | _model
        _chain_learning = learning_prompt | _model

    return _model, _chain_patient, _chain_learning, _chain_casual

# ===============================
# MAIN RESPONSE FUNCTION
# ===============================
def get_bot_response(user_ques):

    global USER_NAME, NAME_UPDATED

    # Get current time for general knowledge context
    current_time = datetime.datetime.now().strftime("%A, %d %B %Y, %I:%M %p")

    try:
        if not isinstance(user_ques, str):
            user_ques = str(user_ques)

        user_ques = user_ques.strip()

        if not user_ques:
            return "🙂 Please type your question."

        # 🚨 Emergency First
        if check_emergency(user_ques):
            return """🚨 **EMERGENCY ALERT**

Your symptoms may indicate a serious medical emergency.
Please call your local emergency number or visit the nearest hospital immediately.
"""

        # Detect intent (includes name update)
        intent = detect_intent(user_ques)

        name_updated = NAME_UPDATED
        NAME_UPDATED = False

        # Token safe memory
        memory_context = get_memory_context()[-800:]

        triage_level = smart_triage(user_ques)

        logger.info(f"Intent detected: {intent} | User: {USER_NAME}")

        model, chain_patient, chain_learning, chain_casual = get_model_and_chains()

        short_mode = len(user_ques.split()) <= 4

        # ===============================
        # CASUAL MODE (+ GENERAL KNOWLEDGE)
        # ===============================
        if intent == "casual":

            if name_updated:
                final_output = f"Nice to meet you, {USER_NAME} 🙂 How can I help you today?"
            else:
                response = chain_casual.invoke({
                    "history": memory_context,
                    "question": user_ques,
                    "user_name": USER_NAME,
                    "date_time": current_time,
                    "short_mode": short_mode
                })

                final_output = response.content.strip()

        # ===============================
        # LEARNING MODE
        # ===============================
        elif intent == "learning":

            retrieved_context = safe_retrieve(user_ques) or "General medical knowledge."

            response = chain_learning.invoke({
                "context": retrieved_context,
                "question": user_ques,
                "user_name": USER_NAME
            })

            final_output = response.content.strip()

            if "educational" not in final_output.lower():
                final_output += "\n\n*Educational information only.*"

        # ===============================
        # PATIENT MODE
        # ===============================
        else:

            retrieved_context = safe_retrieve(user_ques) or "General medical knowledge."

            response = chain_patient.invoke({
                "history": memory_context,
                "context": retrieved_context,
                "question": user_ques,
                "user_name": USER_NAME,
                "date_time": current_time
            })

            final_output = response.content.strip()

            if "Severity Level:" in final_output:
                final_output = final_output.split("Severity Level:")[0].strip()

            if "educational purposes only" in final_output.lower():
                final_output = final_output.split("Note:")[0].strip()

            severity_text = get_severity_level(triage_level)
            disclaimer_text = "Note: This information is for educational purposes only and is not a substitute for professional medical advice."

            final_output += f"\n\n{severity_text}\n\n*{disclaimer_text}*"

        update_memory(user_ques, final_output)

        return final_output

    except Exception as e:
        logger.error(f"System error: {e}")
        return "⚠️ System error occurred. Please try again."
