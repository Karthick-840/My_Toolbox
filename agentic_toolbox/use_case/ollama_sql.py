import sqlite3
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# Define the system template
SYSTEM_TEMPLATE = """
You are an AI assistant that generates SQL queries based on user questions. Your task is to convert the user's natural language question into a valid SQL query.
"""

# Initialize the Ollama LLM
llm = Ollama(model="llama3.2-1b", system_prompt=SYSTEM_TEMPLATE)

# Define the prompt template
prompt_template = PromptTemplate(
    input_variables=["question", "context"],
    template="""
User Question: {question}

Context: {context}

Generated SQL Query:
"""
)

# Create the LangChain
chain = LLMChain(llm=llm, prompt=prompt_template)

# Initialize embeddings and vector store
embeddings = OpenAIEmbeddings()
vector_store = FAISS.load_local("vector_store_index", embeddings)

def execute_query(database_path, query):
    """Executes the SQL query on the given database and fetches results."""
    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        return f"Error executing query: {e}"

def format_results_as_markdown(results):
    """Formats query results as a Markdown table."""
    if not results:
        return "No results found."

    headers = [desc[0] for desc in results[0].keys()] if hasattr(results[0], 'keys') else [f"Column {i+1}" for i in range(len(results[0]))]
    markdown_table = "| " + " | ".join(headers) + " |\n"
    markdown_table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in results:
        markdown_table += "| " + " | ".join(map(str, row)) + " |\n"
    return markdown_table

def main():
    # Path to your SQLite database
    database_path = "your_database.db"

    # User question
    user_question = input("Enter your question about the database: ")

    # Generate embeddings for the user's question
    question_embedding = embeddings.embed_query(user_question)

    # Retrieve relevant context from the vector store
    docs = vector_store.similarity_search_by_vector(question_embedding, k=1)
    context = docs[0].page_content if docs else "No relevant context found."

    # Generate the SQL query using LangChain
    generated_query = chain.run({"question": user_question, "context": context})

    # Print the generated SQL query
    print("Generated SQL Query:")
    print(generated_query)

    # Execute the query and fetch results
    results = execute_query(database_path, generated_query)

    # Format results as Markdown
    if isinstance(results, str):  # If an error occurred
        print(results)
    else:
        markdown_output = format_results_as_markdown(results)
        print("\nResults in Markdown format:")
        print(markdown_output)

if __name__ == "__main__":
    main()
