import os
import sys
from dotenv import load_dotenv
import chromadb
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings  # HuggingFace import karo

# Load from .env
load_dotenv()

pdf_path = "medical_books/"
documents = []

sys.stderr = open(os.devnull, "w")  # Hide chromadb output

# Load PDFs
for pdf in os.listdir(pdf_path):
    if pdf.endswith(".pdf"):
        loader = PyPDFLoader(os.path.join(pdf_path, pdf))
        docs = loader.load()
        documents.extend(docs)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
docs = text_splitter.split_documents(documents)

# Store in ChromaDB
DB_PATH = "medical_chromadb/"
if not os.path.exists(DB_PATH):
    chroma_client = chromadb.PersistentClient(path=DB_PATH)

    vectorstore = Chroma(
        collection_name="medical_docs",
        embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2"),  # Correct model for 768 dimensions
        client=chroma_client
    )

    for i in range(0, len(docs), 100):
        vectorstore.add_documents(docs[i:i + 100])

    print("✅ Medical documents embedded into ChromaDB using correct HuggingFace embeddings (768 dimensions)!")
else:
    print("✅ Loading existing ChromaDB...")
    chroma_client = chromadb.PersistentClient(path=DB_PATH)
    vectorstore = Chroma(
        collection_name="medical_docs",
        embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2"),  # Correct model for 768 dimensions
        persist_directory=DB_PATH
    )

retriever = vectorstore.as_retriever(search_kwargs={"k": 15})
