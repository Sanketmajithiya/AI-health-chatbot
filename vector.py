import os
import sys
import chromadb
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
import streamlit as st

def load_retriever():
    load_dotenv()
    
    pdf_path = "medical_books/"
    documents = []

    if not os.path.exists(pdf_path):
        raise FileNotFoundError("PDF folder missing!")

    sys.stderr = open(os.devnull, "w")  # Hide chromadb output

    for pdf in os.listdir(pdf_path):
        if pdf.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(pdf_path, pdf))
            docs = loader.load()
            documents.extend(docs)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = text_splitter.split_documents(documents)

    DB_PATH = "medical_chromadb/"
    chroma_client = chromadb.PersistentClient(path=DB_PATH)

    vectorstore = Chroma(
        collection_name="medical_docs",
        embedding_function=HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2"),
        client=chroma_client,
        persist_directory=DB_PATH
    )

    if not os.listdir(DB_PATH):
        for i in range(0, len(docs), 100):
            vectorstore.add_documents(docs[i:i + 100])

    return vectorstore.as_retriever(search_kwargs={"k": 15})
