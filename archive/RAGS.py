

import os
import sqlite3
print(sqlite3.sqlite_version)



    
    # Fetch data from API and create DataFrame
    eco_ind = pd.DataFrame(get_jsonparsed_data(ticker, api_key, exchange))
    
    # Save the DataFrame to CSV
    eco_ind.to_csv(file_path, index=False)
    print("Data fetched from API and saved to file:")




preprocessed_economic_df = preprocess_economic_data(eco_ind)
preprocessed_economic_df

preprocessed_economic_df.to_csv(file_path, index=False)
print("Data fetched from API and saved to file and processed:")

# Storing the Pre-Processed Data into CSV

from langchain_community.embeddings import HuggingFaceEmbeddings
hg_embeddings = HuggingFaceEmbeddings()

from langchain.document_loaders import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
loader_eco = CSVLoader('eco_ind.csv')
documents_eco = loader_eco.load()

# Get your splitter ready
text_splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=5)

# Split your docs into texts
texts_eco = text_splitter.split_documents(documents_eco)

# Embeddings
embeddings = HuggingFaceEmbeddings()

print(embeddings)

# # Building the Vector DB for RAG


from langchain.vectorstores import Chroma
persist_directory = 'docs/chroma_rag/'


economic_langchain_chroma = Chroma.from_documents(
    documents=texts_eco,
    collection_name="economic_data",
    embedding=hg_embeddings,
    persist_directory=persist_directory
)

question = "Microsoft(MSFT)"
docs_eco = economic_langchain_chroma.similarity_search(question,k=3)




from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFaceHub
from IPython.display import display, Markdown
import os
import warnings
warnings.filterwarnings('ignore')

llm = HuggingFaceHub(
    repo_id="tiiuae/falcon-7b-instruct",
    model_kwargs={"temperature": 0.1},
)

retriever_eco = economic_langchain_chroma.as_retriever(search_kwargs={"k":2})
qs="Microsoft(MSFT) Financial Report"
template = """You are a Financial Market Expert and Get the Market Economic Data and Market News about Company and Build the Financial Report for me.
              Understand this Market Information {context} and Answer the Query for this Company {question}. i just need the data into Tabular Form as well."""

PROMPT = PromptTemplate(input_variables=["context","question"], template=template)
qa_with_sources = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff",chain_type_kwargs = {"prompt": PROMPT}, retriever=retriever_eco, return_source_documents=True)
llm_response = qa_with_sources({"query": qs})
    
print(llm_response)

