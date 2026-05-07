# app.py (Example usage)

import os
from models import Document, EmbeddingConfig, ChromaDBConfig, QdrantDBConfig
from embeddings import GeminiEmbedder
from vector_databases import ChromaDB, QdrantDB

# --- Configuration ---
# Replace with your actual API key or load from environment variable
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY", "GEMINI_API_KEY_HERE")

# Embedding configuration
embedding_config = EmbeddingConfig(api_key=GEMINI_API_KEY)
gemini_embedder = GeminiEmbedder(config=embedding_config)

# Sample documents
documents = [
    Document(content="Operating the Climate Control System. Your Googlecar has a climate control system that allows you to adjust the temperature and airflow in the car."),
    Document(content="Your Googlecar has a large touchscreen display that provides access to a variety of features, including navigation, entertainment, and climate control."),
    Document(content="Shifting Gears. Your Googlecar has an automatic transmission. To shift gears, simply move the shift lever to the desired position."),
    Document(content="AI is starting to address climate challenges in three key areas: providing people and organizations with better information to make more sustainable choices, delivering improved predictions to help adapt to climate change, and finding recommendations to optimize climate action for high-impact applications."),
    Document(content="Managing the environmental impact of AI. While scaling these applications of AI and finding new ways to use it to accelerate climate action is crucial, we need to build AI responsibly and manage the environmental impact associated with it.")
]

# --- ChromaDB Usage ---
print("\n--- Using ChromaDB ---")
chroma_config = ChromaDBConfig(collection_name="google_car_manual", persist_directory="./chroma_data")
chroma_db = ChromaDB(config=chroma_config, embedder=gemini_embedder)
chroma_db.add_documents(documents)

query_chroma = "How do you use the touchscreen in the Google car?"
chroma_results = chroma_db.search(query_chroma, limit=2)
for i, result in enumerate(chroma_results):
    print(f"Chroma Result {i+1} (Score: {result.score:.4f}): {result.document.content[:100]}...")

# --- QdrantDB Usage ---
print("\n--- Using QdrantDB ---")
qdrant_config = QdrantDBConfig(collection_name="google_blog_posts", location=":memory:") # In-memory Qdrant
qdrant_db = QdrantDB(config=qdrant_config, embedder=gemini_embedder)
qdrant_db.add_documents(documents)

query_qdrant = "How can AI address climate challenges?"
qdrant_results = qdrant_db.search(query_qdrant, limit=2)
for i, result in enumerate(qdrant_results):
    print(f"Qdrant Result {i+1} (Score: {result.score:.4f}): {result.document.content[:100]}...")