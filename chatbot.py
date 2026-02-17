from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from vector import load_retriever
import os
from dotenv import load_dotenv

load_dotenv()

# ===============================
# Lazy loaded global variables
# ===============================
_retriever = None
_model = None
_chain = None


# ===============================
# Lazy Retriever Loader
# ===============================
def get_retriever():
    global _retriever

    if _retriever is None:
        print("[DEBUG] Loading retriever...")
        _retriever = load_retriever()

    return _retriever


# ===============================
# Lazy Model + Chain Loader
# ===============================
def get_model_and_chain():
    global _model, _chain

    if _model is None:

        model_name = os.getenv("GROQ_MODEL") or "llama-3.3-70b-versatile"
        temperature = float(os.getenv("TEMPERATURE") or "0.3")
        api_key = os.getenv("GROQ_API_KEY")

        print(f"[DEBUG] Model: {model_name}")
        print(f"[DEBUG] API key loaded: {'YES' if api_key else 'NO'}")

        _model = ChatGroq(
            model=model_name,
            temperature=temperature,
            groq_api_key=api_key
        )

        prompt = ChatPromptTemplate.from_template("""
You are a helpful and knowledgeable medical assistant.

- Always use provided context.
- Be accurate and professional.
- Do NOT hallucinate.

Context:
{context}

Question:
{question}

Answer:
""")

        _chain = prompt | _model

    return _model, _chain


# ===============================
# MAIN RESPONSE FUNCTION
# ===============================
def get_bot_response(user_ques):

    try:
        print(f"[DEBUG] Question: {user_ques}")

        if not isinstance(user_ques, str):
            user_ques = str(user_ques)

        retriever = get_retriever()

        docs = retriever.invoke(user_ques)
        print(f"[DEBUG] Retrieved docs: {len(docs)}")

        context = "\n\n".join([doc.page_content for doc in docs])

        model, chain = get_model_and_chain()

        response = chain.invoke({
            "context": context,
            "question": user_ques
        })

        return response.content

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return f" Error: {str(e)}"
