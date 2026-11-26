
import csv

# Load sample data (a restaurant menu of items)
with open('menu_items.csv') as file:
    lines = csv.reader(file)

    # Store the name of the menu items in this array. In Chroma, a "document" is a string i.e. name, sentence, paragraph, etc.
    documents = []

    # Store the corresponding menu item IDs in this array.
    metadatas = []

    # Each "document" needs a unique ID. This is like the primary key of a relational database. We'll start at 1 and increment from there.
    ids = []
    id = 1

    # Loop thru each line and populate the 3 arrays.
    for i, line in enumerate(lines):
        if i==0:
            # Skip the first row (the column headers)
            continue

        documents.append(line[1])
        metadatas.append({"item_id": line[0]})
        ids.append(str(id))
        id+=1
# Install chromadb
%pip install chromadb

# Install sentence transformers
# This is used to convert text to vector embeddings. In other words, it converts text to a bunch of numbers that represent the 'meaning' of the text.
%pip install -U sentence-transformers
# Install Gemini Pro
%pip install google-generativeai
# Reference: https://docs.trychroma.com/getting-started

import chromadb
from chromadb.utils import embedding_functions

# Instantiate chromadb instance. Data is stored in memory only.
# chroma_client = chromadb.Client()

# Instantiate chromadb instance. Data is stored on disk (a folder named 'my_vectordb' will be created in the same folder as this file).
chroma_client = chromadb.PersistentClient(path="my_vectordb")
# Get your API Key at https://console.cloud.google.com/ or https://aistudio.google.com/app/apikey
google_ef  = embedding_functions.GoogleGenerativeAiEmbeddingFunction(api_key="[your key]")

# Use this to delete the database
# chroma_client.delete_collection(name="my_collection")

# Create the collection, aka vector database. Or, if database already exist, then use it. Specify the model that we want to use to do the embedding.
collection = chroma_client.get_or_create_collection(name="my_collection", embedding_function=google_ef)
# Add all the data to the vector database. ChromaDB automatically converts and stores the text as vector embeddings. This may take a few minutes.
collection.update(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)
# Query the vector database

# Query mispelled word: 'vermiceli'. Expect to find the correctly spelled 'vermicelli' item
results = collection.query(
    query_texts=["vermiceli"],
    n_results=5,
    include=['documents', 'distances', 'metadatas']
)
print(results['documents'])

# Query word variation: 'donut'. Expect to find the 'doughnut' item
results = collection.query(
    query_texts=["donut"],
    n_results=5,
    include=['documents', 'distances', 'metadatas']
)
print(results['documents'])

# Query similar meaning: 'shrimp'. Expect to find the 'prawn' items
results = collection.query(
    query_texts=["shrimp"],
    n_results=5,
    include=['documents', 'distances', 'metadatas']
)
print(results['documents'])
[['Melon and Vermicelli', 'Sesame Ball', 'Fried Turnip Ball', 'Braised Noodle', 'Vegetable Tempura']]
[['Chinese Doughnut', 'Sesame Ball', 'Soda', 'Happy Ball', 'Toons Pan Cake']]
[['Salt and Pepper Vegan Prawns', 'Vegetable Tempura', 'Plain Steamed Rice', 'Vegan Prawns with Mixed Vegetables', 'Vegan Prawns and Mushrooms and Vegetables']]