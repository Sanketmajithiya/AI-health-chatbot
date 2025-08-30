from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from vector import retriever
import os
from dotenv import load_dotenv

load_dotenv()  # Load keys

model = ChatOpenAI(
    model="llama3-70b-8192",  # Or use "mixtral-8x7b-32768"
    temperature=0.3
)

prompt = ChatPromptTemplate.from_template(
    """
    You are a helpful and knowledgeable medical assistant. Your task is to provide accurate and context-aware answers based on the provided medical literature.

    - Always use the provided **context** to answer the user's **question**.
    - Be clear, concise, and professional in your responses.
    - Do not make up information or guess beyond the given context.

    Context:
    {context}

    Question:
    {question}

    Answer:
    """
)

chain = prompt | model

def get_bot_response(user_ques):
    if not isinstance(user_ques, str):
        user_ques = str(user_ques)

    # Documents lekar aao vectorstore se
    docs = retriever.get_relevant_documents(user_ques)

    # Context ready karo
    context = "\n\n".join([doc.page_content for doc in docs])

    # Model ko sahi format mein input do using chain
    response = chain.invoke({
        "context": context,
        "question": user_ques
    })

    return response.content




