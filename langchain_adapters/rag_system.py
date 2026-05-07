# rag_system.py

from langchain.llms import HuggingFaceHub
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from utils import setup_chroma_collection, load_documents_from_csv, get_embedding_model
from langchain.docstore.document import Document
import os

class RAGSystem:
    def __init__(self, repo_id="tiiuae/falcon-7b-instruct", persist_directory="./chroma_db"):
        self.llm = HuggingFaceHub(
            repo_id=repo_id,
            model_kwargs={"temperature": 0.1, "max_new_tokens": 1000},
            huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN") # Ensure this env var is set
        )
        self.persist_directory = persist_directory
        self.vectorstore = None
        self.qa_chain = None

    def initialize_vectorstore(self, csv_file_path, collection_name="financial_data_collection"):
        """Initializes the ChromaDB vectorstore with documents from a CSV."""
        documents = load_documents_from_csv(csv_file_path, page_content_col='page_content')
        # Langchain Document objects already have 'page_content' and 'metadata'.
        # The load_documents_from_csv utility function creates these.
        self.vectorstore = setup_chroma_collection(
            persist_directory=self.persist_directory,
            collection_name=collection_name,
            documents=documents
        )
        print(f"Vectorstore initialized with {len(documents)} documents.")

    def setup_qa_chain(self):
        """Sets up the RetrievalQA chain with a custom prompt."""
        if not self.vectorstore:
            raise ValueError("Vectorstore not initialized. Call initialize_vectorstore first.")

        # Define the prompt template
        template = """
        You are an AI assistant specialized in financial reporting. Use the following context to answer the question concisely and accurately.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.

        Context: {context}

        Question: {question}
        """
        QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context", "question"], template=template)

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(),
            chain_type_kwargs={"prompt": QA_CHAIN_PROMPT},
            return_source_documents=True
        )
        print("RetrievalQA chain set up.")

    def query(self, question):
        """Executes a query against the RAG system."""
        if not self.qa_chain:
            raise ValueError("QA chain not set up. Call setup_qa_chain first.")
        
        print(f"Querying: {question}")
        result = self.qa_chain({"query": question})
        return result
