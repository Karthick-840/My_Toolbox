# financial_reporter.py

import os
from financial_data_processor import FinancialDataProcessor
from rag_system import RAGSystem

class FinancialReporter:
    def __init__(self, fmp_api_key_name="FMP_API_KEY", hf_api_token_name="HUGGINGFACEHUB_API_TOKEN", 
                 model_repo_id="tiiuae/falcon-7b-instruct", data_output_dir="data", chroma_persist_dir="./chroma_db"):
        # Ensure API keys are set as environment variables.
        # For local testing, you might temporarily set them like:
        # os.environ["FMP_API_KEY"] = "YOUR_FMP_API_KEY_HERE"
        # os.environ["HUGGINGFACEHUB_API_TOKEN"] = "YOUR_HUGGINGFACE_API_TOKEN_HERE"
        # It's highly recommended to set them as actual environment variables in your system.

        self.data_processor = FinancialDataProcessor(api_key_name=fmp_api_key_name)
        self.rag_system = RAGSystem(repo_id=model_repo_id, persist_directory=chroma_persist_dir)
        self.data_output_dir = data_output_dir
        self.chroma_persist_dir = chroma_persist_dir

    def generate_economic_report(self, question):
        """Generates a report based on economic indicators."""
        print("--- Generating Economic Report ---")
        economic_csv_path = self.data_processor.process_and_save_economic_indicators(self.data_output_dir)
        
        if economic_csv_path:
            self.rag_system.initialize_vectorstore(economic_csv_path, collection_name="economic_indicators_collection")
            self.rag_system.setup_qa_chain()
            response = self.rag_system.query(question)
            return response
        else:
            return {"answer": "Could not process economic indicators.", "source_documents": []}

    def generate_company_financial_report(self, symbol, question):
        """Generates a report based on a specific company's financial data."""
        print(f"--- Generating Financial Report for {symbol} ---")
        company_csv_path = self.data_processor.process_and_save_company_data(symbol, self.data_output_dir)

        if company_csv_path:
            self.rag_system.initialize_vectorstore(company_csv_path, collection_name=f"{symbol}_financial_data_collection")
            self.rag_system.setup_qa_chain()
            response = self.rag_system.query(question)
            return response
        else:
            return {"answer": f"Could not process financial data for {symbol}.", "source_documents": []}
