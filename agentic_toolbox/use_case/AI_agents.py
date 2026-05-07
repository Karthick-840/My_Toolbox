import sqlite3
from langchain.memory import ConversationBufferMemory
from PyPDF2 import PdfReader
import pandas as pd
from ollama import Ollama  # Assuming you have an Ollama library or API client
# u can use firecraw for website scrapping
# Initialize the database
def initialize_database(database=None):
    if not database:
        database = "chat_history.db"
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS {database} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            message TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# Save a message to the database
def save_message_to_db(sender, message,database):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO {database} (sender, message) VALUES (?, ?)""", (sender, message))
    conn.commit()
    conn.close()

# Retrieve chat history from the database
def get_chat_history_from_db():
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()
    cursor.execute("SELECT sender, message FROM chat_history")
    history = cursor.fetchall()
    conn.close()
    return history

# Initialize the Ollama model
class OllamaChatModel:
    def __init__(self, model_name="default_model"):
        self.model = Ollama(model_name=model_name)
        self.memory = ConversationBufferMemory()

    def chat(self, user_message):
        # Add user message to memory and database
        self.memory.chat_memory.add_user_message(user_message)
        save_message_to_db("user", user_message)

        # Get AI response
        ai_response = self.model.generate(user_message)
        self.memory.chat_memory.add_ai_message(ai_response)
        save_message_to_db("ai", ai_response)

        return ai_response

# Example usage
if __name__ == "__main__":
    initialize_database()

    # Create an instance of the OllamaChatModel
    chat_model = OllamaChatModel(model_name="your_ollama_model")

    # Simulate a chat
    user_message = "Hello, how are you?"
    print(f"User: {user_message}")
    ai_response = chat_model.chat(user_message)
    print(f"AI: {ai_response}")

    # Retrieve and print chat history from the database
    chat_history = get_chat_history_from_db()
    print("\nChat History:")
    for sender, message in chat_history:
        print(f"{sender}: {message}")


        class TableExtractionAgent:
            def __init__(self, model_name="table_extraction_model"):
                self.model = Ollama(model_name=model_name)

            def extract_tables_from_pdf(self, pdf_path):
                # Read the PDF file
                reader = PdfReader(pdf_path)
                tables = []

                # Iterate through pages and extract tables
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        # Use the AI model to identify and extract tables
                        table_data = self.model.generate(f"Extract tables from the following text:\n{text}")
                        if table_data:
                            try:
                                # Convert the extracted table data into a DataFrame
                                table_df = pd.read_csv(pd.compat.StringIO(table_data))
                                tables.append(table_df)
                            except Exception as e:
                                print(f"Error processing table data: {e}")

                return tables

        # Example usage
        if __name__ == "__main__":
            # Initialize the TableExtractionAgent
            table_agent = TableExtractionAgent(model_name="your_table_extraction_model")

            # Path to the PDF file
            pdf_file_path = "example.pdf"

            # Extract tables
            extracted_tables = table_agent.extract_tables_from_pdf(pdf_file_path)

            # Print extracted tables
            for idx, table in enumerate(extracted_tables):
                print(f"\nTable {idx + 1}:")
                print(table)