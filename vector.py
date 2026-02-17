import os
import sys
import chromadb
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader, PDFPlumberLoader, PDFMinerLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
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
            pdf_file_path = os.path.join(pdf_path, pdf)
            loaded = False
            
            # Try multiple parsers as fallback
            parsers = [
                ("PyPDF", PyPDFLoader),
                ("PDFPlumber", PDFPlumberLoader),
                ("PDFMiner", PDFMinerLoader)
            ]
            
            for parser_name, ParserClass in parsers:
                try:
                    loader = ParserClass(pdf_file_path)
                    docs = loader.load()
                    if docs:  # Only add if we got content
                        documents.extend(docs)
                        print(f"[OK] Successfully loaded {pdf} using {parser_name}")
                        loaded = True
                        break
                except Exception as e:
                    continue  # Try next parser
            
            if not loaded:
                print(f"[WARN] Could not load {pdf} with any parser")

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

    # Load PDFs into database only if it's empty (first run)
    if not os.listdir(DB_PATH) or len(os.listdir(DB_PATH)) == 0:
        print("[INFO] First run detected - Loading PDFs into vector database...")
        for i in range(0, len(docs), 100):
            vectorstore.add_documents(docs[i:i + 100])
        print("[OK] Vector database initialized successfully!")
    else:
        print("[INFO] Using existing vector database")

    return vectorstore.as_retriever(search_kwargs={"k": 15})
