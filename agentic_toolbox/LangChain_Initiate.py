import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Set OPENAI_API_KEY before running this script.")


# Create First reposne
llm = ChatOpenAI()

llm.invoke("what is docker and how is it useful for deployment?")


# Create First chain in LCEL is now the default way to create chains in LangChain. It has a more pipeline-like syntax and allows you to modify already-existing chains.

prompt = ChatPromptTemplate.from_messages([("sysmtem","You are an English-French transaltor that returns whatever the user says from English to French"),
                                           ("user","{input}")])

chain = prompt | llm


chain.invoke({
    "input": "i enjoy going to rock concerts"
    })


# add output parser to the chain

from langchain_core.output_parsers import StrOutputParser

output_parser = StrOutputParser()

chain = prompt | llm | output_parser

chain.invoke({"input": "my friend robert has a blue cat"})

llm.invoke("what is new in langchain 0.1.0?")

# Create a Retrvela Chain

"""

## 3.1 Load the source documents

First, we will have to load the documents that will enrich our LLM prompt. We will use [this blog post](https://blog.langchain.dev/langchain-v0-1-0/) from LangChain's official website explaining the new release. OpenAI's models were not trained on this content, so the only way to ask questions about it is to build a RAG chain.

The first thing to do is to load the blog content to our vector store. We will use beautiful soup to scrap the blog post. Then we will store it in a FAISS vector store.

"""

from langchain_community.document_loaders import WebBaseLoader

loader = WebBaseLoader("https://blog.langchain.dev/langchain-v0-1-0/")

docs = loader.load()

docs

from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()


from langchain_community.vectorstores import FAISS
from langchain.text_splitter  import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)


documents

vectorstore = FAISS.from_documents(documents, embeddings)

## 3.2 Create a Context-Aware LLM Chain

"""
Here we create a chain that will answer a question given a context. For now, we are passing the context manually, but in the next step we will pass in the documents fetched from the vector store we created above 👆

"""

# create chain for documents

from langchain.chains.combine_documents import create_stuff_documents_chain

template = """"Answer the following question based only on the provided context:

<context>
{context}
</context>

Question: {input}
"""
prompt = ChatPromptTemplate.from_template(template)
document_chain = create_stuff_documents_chain(llm, prompt)