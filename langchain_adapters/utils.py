# utils.py

import os
import pandas as pd
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document

def get_api_key(key_name):
    """Fetches API key from environment variables."""
    api_key = os.getenv(key_name)
    if not api_key:
        raise ValueError(f"API key for {key_name} not found in environment variables.")
    return api_key

def get_embedding_model(model_name="sentence-transformers/all-MiniLM-L6-v2"):
    """Initializes and returns a HuggingFace embeddings model."""
    return HuggingFaceEmbeddings(model_name=model_name)

def setup_chroma_collection(persist_directory, collection_name, documents):
    """
    Sets up a ChromaDB collection with provided documents.
    If the collection already exists, it is loaded.
    """
    embedding_model = get_embedding_model()
    try:
        # Try to load existing collection
        vectordb = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory=persist_directory
        )
        print(f"Loaded existing ChromaDB collection: {collection_name}")
    except Exception:
        # If loading fails (e.g., collection does not exist), create a new one
        vectordb = Chroma.from_documents(
            documents=documents,
            embedding=embedding_model,
            collection_name=collection_name,
            persist_directory=persist_directory
        )
        print(f"Created new ChromaDB collection: {collection_name}")
    return vectordb

def load_documents_from_csv(file_path, page_content_col='Description'):
    """Loads documents from a CSV file into Langchain Document format."""
    df = pd.read_csv(file_path)
    documents = []
    for _, row in df.iterrows():
        # Customize this based on your CSV structure
        # Assuming 'Description' or similar column for page content
        page_content = str(row[page_content_col])
        metadata = row.drop(page_content_col).to_dict()
        documents.append(Document(page_content=page_content, metadata=metadata))
    print(f"Loaded {len(documents)} documents from {file_path}")
    return documents
