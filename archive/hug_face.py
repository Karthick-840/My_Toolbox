# leanr in all pytorch tensorflow flad

from transformers import pipeline
#from transformers import AutoTokenizer, AutoModelForSeqeunceClassfication, BertTokenizer, # find time for that.,

classifier = pipeline("sentiment-analysis")

res =  classifier("I ve been waiting for hugging face course my whole life")

print(res)


generator = pipeline("text-generation",model="distilgpt2")

res = generator("In this course, we will teach you how to", max_length=30,num_return_sequences=2)
print(res)

# pipeline("zero-shot-classification")

#Develop AI tool. 

import torch
import torch.nn.functional as F

# Use spaces in hugging face to deploy models to check the files
#upload the image to the space and check the files in the space to create a audio file

from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.embeddings import Embeddings
from langchain.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader, DirectoryLoader, pythoncodetextsplitter
from langchain_community.document_loaders import UnstructuredHTMLLoader

loader = UnstructuredHTMLLoader("example_data/fake-content.html")
from langchain_community.document_loaders import UnstructuredMarkdownLoader
markdown_path = "../../../../../README.md"
loader = UnstructuredMarkdownLoader(markdown_path)
!pip install pypdf

from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("example_data/layout-parser-paper.pdf", extract_images=True)
pages = loader.load_and_split()

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

faiss_index = FAISS.from_documents(pages, OpenAIEmbeddings())
docs = faiss_index.similarity_search("How will the community be engaged?", k=2)
for doc in docs:
    print(str(doc.metadata["page"]) + ":", doc.page_content[:300])


"""
6:57 - Level 1: Character Split
16:04 - Level 2: Recursive Character Split
20:59 - Level 3: Document Specific Splitting
32:10 - Level 4: Semantic Splitting (With Embeddings)
48:02 - Level 5: Agentic Splitting
1:02:47 - Bonus Level: Alternative Representation



use ragas for retriveal testing
"""
from langchain_community.document_loaders.csv_loader import CSVLoader

loader = CSVLoader(file_path='./example_data/mlb_teams_2012.csv', csv_args={
    'delimiter': ',',
    'quotechar': '"',
    'fieldnames': ['MLB Team', 'Payroll in millions', 'Wins']
})

data = loader.load()

loader = CSVLoader(file_path='./example_data/mlb_teams_2012.csv', source_column="Team")

data = loader.load()

def character_text_splitting(text, embedding_model: Embeddings, chunk_size=100, chunk_overlap=20,separator='',strip_whitespace=False):
    """
    Splits the input text into smaller chunks of specified size using CharacterTextSplitter.
    
    Args:
        text (str): The input text to be split.
        embedding_model (Embeddings): The embedding model to be used.
        chunk_size (int): The size of each chunk.
        chunk_overlap (int): The overlap between consecutive chunks.

    Returns:
        list: A list of text chunks.
    """
    text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap,separator='',strip_whitespace=False)
    chunks = text_splitter.create_documents([text])
    return chunks

def recursive_character_text_splitting(text, embedding_model: Embeddings, chunk_size=100, chunk_overlap=20):
    """
    Splits the input text into smaller chunks recursively using RecursiveCharacterTextSplitter.
    
    Args:
        text (str): The input text to be split.
        embedding_model (Embeddings): The embedding model to be used.
        chunk_size (int): The size of each chunk.
        chunk_overlap (int): The overlap between consecutive chunks.

    Returns:
        list: A list of text chunks.
    """

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_splitter.split_text(text)
    return chunks



def document_specific_splitting(file_path, embedding_model: Embeddings, chunk_size=100, chunk_overlap=20):
    """
    Splits the content of a document into smaller chunks of specified size based on its type.
    
    Args:
        file_path (str): The path to the document file.
        embedding_model (Embeddings): The embedding model to be used.
        chunk_size (int): The size of each chunk.
        chunk_overlap (int): The overlap between consecutive chunks.

    Returns:
        list: A list of text chunks.
    """
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    elif file_path.endswith('.txt'):
        loader = TextLoader(file_path)
    elif file_path.endswith('.md'):
        loader = UnstructuredMarkdownLoader(file_path)
    else:
        raise ValueError("Unsupported file type. Supported types: .pdf, .txt, .md")
    
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = text_splitter.split_documents(documents)
    return chunks


pip install unstructured[pdf]
from langchain_community.document_loaders import UnstructuredPDFLoader
# The unstructured[all-docs] package currently supports loading of text files, powerpoints, html, pdfs, images, and more


from langchain_community.document_loaders import OnlinePDFLoader
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

loader = OnlinePDFLoader("https://arxiv.org/pdf/2302.03803.pdf")

data = loader.load()

data = loader.load()

def semantic_text_splitting(text, embedding_model: Embeddings, similarity_threshold=0.8):
    """
    Splits the input text into semantically meaningful chunks using embeddings and similarity threshold.
    
    Args:
        text (str): The input text to be split.
        embedding_model (Embeddings): The embedding model to be used.
        similarity_threshold (float): The cosine similarity threshold to determine chunk boundaries.

    Returns:
        list: A list of semantically meaningful text chunks.

        Hierarchival clsutering with positonal reward
        find break points between sequencial senteneces
    """

    sentences = text.split('. ', '?', '!')  # Split text into sentences
    sentences = [f"{i}: {sentence}" for i, sentence in enumerate(sentences)]  # Add index to each split
    embeddings = embedding_model.embed_documents(sentences)
    chunks = []
    current_chunk = [sentences[0]]
    # Another idea is to check the chunk 1,2,3 with 4,5,6

    for i in range(1, len(sentences)):
        current_embedding = embedding_model.embed_documents([" ".join(current_chunk)])[0]
        next_embedding = embeddings[i]
        similarity = cosine_similarity([current_embedding], [next_embedding])[0][0]

        if similarity < similarity_threshold:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentences[i]]
        else:
            current_chunk.append(sentences[i])

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


# youtube transcitp to article

# uyunstrucutred pdf is agood resource to start working on it. for financial documents partition pdf is a good option
# agentic model iwth hub.pull.
"""

"""
Summary of Steps to Use Hugging Face for AI Apps
Introduction to Hugging Face:

Hugging Face is a leading AI platform with over 200,000 models used by major companies like Google and Amazon.
It offers models, datasets, and a space for showcasing AI applications.
Understanding the Platform:

Models: Find and test various AI models directly on the platform.
Datasets: Access datasets for training your own models.
Spaces: Deploy and showcase your AI applications easily.
Building an AI App:

Objective: Create an app that converts an image into an audio story.
Components:
Image to Text Model: To interpret the scenario in the uploaded image.
Large Language Model (LLM): To generate a short story based on the interpreted text.
Text to Speech Model: To convert the generated story into audio.
Step-by-Step Implementation:

Step 1: Image to Text Model:

Use Hugging Face to find an image-to-text model (e.g., BLIP).
Create an account and generate an access token.
Set up a Python environment, import libraries, and load the model.
Step 2: Generate Story with LLM:

Use an LLM (like GPT) to create a story based on the description from the image.
Set up the OpenAI API key and create a prompt template.
Step 3: Convert Text to Speech:

Find a text-to-speech model on Hugging Face.
Use the Hugging Face API to convert the generated story into audio.
Step 4: Build User Interface with Streamlit:

Use Streamlit to create a user-friendly interface for uploading images and displaying results.
Connect all components to allow users to upload an image, generate a story, and play the audio.
Running the App:

Launch the Streamlit app and test the functionality by uploading an image.
Verify the generated story and audio output.
Additional Resources:

Explore more tasks and models on Hugging Face by visiting their tasks page.
Consider using low-code platforms like Relevance AI for quicker deployments.
Conclusion:

Hugging Face is a powerful tool for building AI applications.
Encourage experimentation and further learning in AI development.
Final Note
"""