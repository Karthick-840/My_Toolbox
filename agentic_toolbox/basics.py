import os
from openai import OpenAI


token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o-mini"

# client = OpenAI(
#     base_url=endpoint,
#     api_key=token,
# )

# response = client.chat.completions.create(
#     messages=[
#         {
#             "role": "system",
#             "content": "You are a helpful assistant.",
#         },
#         {
#             "role": "user",
#             "content": "What is the capital of France?",
#         }
#     ],
#     temperature=1.0,
#     top_p=1.0,
#     max_tokens=1000,
#     model=model_name
# )

# print(response.choices[0].message.content)

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(base_url=endpoint,api_key=token,model_name=model_name )

# response  = llm.invoke("what is docker and how is it useful for deployment?")
# print(response.content)


prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an Tech-Elementary school translator that return whatever the user says in simple english understandable to school childresn"),
    ("user", "{input}")
])

# chain = prompt | llm
# response  =  chain.invoke({"input": "what is docker and how is it useful for deployment?"})
# print(response.content)

# # add output parser to the chain

# output_parser = StrOutputParser()
# chain = prompt | llm | output_parser

# response = chain.invoke({"input": "what is docker and how is it useful for deployment?"})
# print(response)
os.environ['USER_AGENT'] = 'myagent'

# token = os.environ["GITHUB_TOKEN"]
# endpoint = "https://models.inference.ai.azure.com"
# model_name = "text-embedding-3-large"

from langchain_community.document_loaders import WebBaseLoader
# Set the USER_AGENT environment variable
loader = WebBaseLoader("https://www.nvidia.com/en-us/")

docs = loader.load()
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(base_url=endpoint,api_key=token,model = "text-embedding-3-large")

from langchain_community.vectorstores import FAISS
from langchain.text_splitter  import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)
vectorstore = FAISS.from_documents(documents, embeddings)

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

# from langchain_core.documents import Document

# response = document_chain.invoke({
#     "input": "what is latest langchain 0.1.0?",
#     "context": [Document(page_content="langchain 0.1.0 is the new version of a llm app development framework.")]
# })

# print(response)

# create retrieval chain



# conversational retrieval chain

from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}"),
    ("user", "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation")
])
retriever = vectorstore.as_retriever()

retriever_chain = create_history_aware_retriever(llm, retriever, prompt)

from langchain_core.messages import HumanMessage, AIMessage

chat_history = [
    HumanMessage(content="Is there anything new ?"),
    AIMessage(content="Yes!")
]

response = retriever_chain.invoke({
    "chat_history": chat_history,
    "input": "Tell me more about it!"
})


print(response)
response['answer']

from langchain.chains import create_retrieval_chain

retriever = vectorstore.as_retriever()
retrieval_chain = create_retrieval_chain(retriever, document_chain)

response = retrieval_chain.invoke({
    "input": "what is latest news for the collaborations with Lenovo of the company?"
})
print(response["answer"])

prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer the user's questions based on the below context:\n\n{context}"),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}")
])

document_chain = create_stuff_documents_chain(llm, prompt)

conversational_retrieval_chain = create_retrieval_chain(retriever_chain, document_chain)

response = conversational_retrieval_chain.invoke({
    'chat_history': [],
    "input": "What is langchain 0.1.0 about?"
})

# simulate conversation history

chat_history = [
    HumanMessage(content="Is there anything new about Langchain 0.1.0?"),
    AIMessage(content="Yes!")
]

response = conversational_retrieval_chain.invoke({
    'chat_history': chat_history,
    "input": "Tell me more about it!"
})

response['answer']