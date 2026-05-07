import langchain
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM
from langchain_community.llms import OpenAI
from langchain.prompts import PromptTemplate
import pandas as pd
import io
import os

def load_and_split_pdf(pdf_path):
    """Loads a PDF and splits it into text chunks."""
    print(f"Loading PDF from: {pdf_path}")
    try:
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        print(f"PDF loaded successfully. Number of pages: {len(documents)}")
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        text_chunks = text_splitter.split_documents(documents)
        print(f"PDF split into {len(text_chunks)} text chunks.")
        return text_chunks
    except Exception as e:
        print(f"Error loading and splitting PDF: {e}")
        return []

def select_llm():
    """Selects the LLM to use (Ollama or OpenAI)."""
    try:
        llm = OllamaLLM(model="deepseek-r1:latest")  # Adjust model name as needed
        _ = llm.invoke("test") #use invoke instead of __call__
        print("Using local Ollama model: deepseek-r1")
        return llm
    except Exception as e:
        print(f"Ollama or deepseek-r1 not found: {e}. Using OpenAI.")
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            openai_api_key = input("Enter your OpenAI API key: ")
        return OpenAI(openai_api_key=openai_api_key, temperature=0.2)

def create_extraction_chain(llm):
    """Creates the LLMChain for table extraction."""
    prompt_template = """
    You are an expert in extracting tables from financial documents. 
    Given the following text from a Form 26AS, extract the table data and return it as a comma-separated value (CSV) string.

    Text:
    {text}

    CSV:
    """
    prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
    print("Extraction chain created.")
    return RunnableSequence([prompt, llm])

def extract_csv_from_chunks(chain, text_chunks):
    """Extracts CSV data from text chunks using the LLMChain."""
    csv_data = ""
    print("Starting CSV extraction from text chunks.")
    for i, text in enumerate(text_chunks):
        print(f"Processing chunk {i + 1}/{len(text_chunks)}.")
        output = chain.run(text=text.page_content)
        csv_data += output + "\n"
    print("CSV extraction complete.")
    return csv_data

def csv_to_dataframe(csv_string):
    """Converts a CSV string to a Pandas DataFrame."""
    if csv_string.strip():
        try:
            print("Attempting to convert CSV string to DataFrame.")
            df = pd.read_csv(io.StringIO(csv_string))
            print("CSV string successfully converted to DataFrame.")
            return df
        except pd.errors.ParserError:
            print("Error parsing CSV data. The output from the LLM could not be converted to a table.")
            return None
    else:
        print("No table data extracted from the PDF.")
        return None

def extract_table_from_form26as(pdf_path):
    """Main function to extract table data from a Form 26AS PDF."""
    try:
        text_chunks = load_and_split_pdf(pdf_path)
        if not text_chunks:
            return None  # Return None if PDF loading or splitting failed.
        llm = select_llm()
        chain = create_extraction_chain(llm)
        csv_string = extract_csv_from_chunks(chain, text_chunks)
        return csv_to_dataframe(csv_string)
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Example usage:
pdf_file_path = "CAHPK8403J-2025.pdf"
extracted_df = extract_table_from_form26as(pdf_file_path)

if extracted_df is not None:
    print(extracted_df)

    # pip install -U langchain langchain-community langchain-ollama pandas pypdf

#     python3 form26as_extract.py
