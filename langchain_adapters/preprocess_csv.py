import pandas as pd
from langchain.document_loaders import CSVLoader

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document  # Import the Document class
#from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import concurrent.futures

class LangChainPreprocess:
    def __init__(self, api_key):
        self.api_key = api_key
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=5)
        self.embeddings = HuggingFaceEmbeddings()

    def process_document(self, document_text):
        """
        Splits the document text into chunks and returns embeddings for each chunk.
        """
        document = Document(page_content=document_text)
        # Split the document into chunks
        texts = self.text_splitter.split_documents([document])
        embeddings_result = [self.embeddings.embed_documents([text.page_content]) for text in texts]
    
        return embeddings_result

    def apply(self, df):
        """
        Apply text preprocessing steps on the provided DataFrame.
        Args:
        df (DataFrame): The dataframe containing stock information (or other textual data).
        """
        documents = []

        # Loop through each row of the DataFrame and dynamically construct document text
        for idx, row in df.iterrows():
            doc_text = ""
            for col in df.columns:
                # Append column name and its value
                doc_text += f"{col}: {row[col]}\n"
            documents.append(doc_text)

        # Use ThreadPoolExecutor to run I/O tasks concurrently
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Map the process_document function to each document concurrently
            processed_results = list(executor.map(self.process_document, documents))

        # Return the processed results (embeddings)