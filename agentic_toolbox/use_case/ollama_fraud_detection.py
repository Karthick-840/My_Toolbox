import os
import re
import random
import warnings
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from langchain.vectorstores import Chroma
from langchain.docstore.document import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig, AutoConfig
from torch import cuda, bfloat16
from IPython.display import display, Markdown

# Ensure NLTK resources are downloaded
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')

# -------------------------
# 1. Sample Data Generation
# -------------------------
fraud_statements = [
    "The company reported inflated revenues by including sales that never occurred.",
    "Financial records were manipulated to hide the true state of expenses.",
    "The company failed to report significant liabilities on its balance sheet.",
    "Revenue was recognized prematurely before the actual sales occurred.",
    "The financial statement shows significant discrepancies in inventory records.",
    "The company used off-balance-sheet entities to hide debt.",
    "Expenses were understated by capitalizing them as assets.",
    "There were unauthorized transactions recorded in the financial books.",
    "Significant amounts of revenue were recognized without proper documentation.",
    "The company falsified financial documents to secure a larger loan."
]

non_fraud_statements = [
    "The company reported stable revenues consistent with historical trends.",
    "Financial records accurately reflect all expenses and liabilities.",
    "The balance sheet provides a true and fair view of the company’s financial position.",
    "Revenue was recognized in accordance with standard accounting practices.",
    "The inventory records are accurate and match physical counts."
]

fraud_data = [{"text": s, "fraud_status": "fraud"} for s in fraud_statements]
non_fraud_data = [{"text": random.choice(non_fraud_statements), "fraud_status": "non-fraud"} for _ in range(20)]
data = fraud_data + non_fraud_data
random.shuffle(data)
df = pd.DataFrame(data)

# -------------------------
# 2. Text Preprocessing
# -------------------------
def clean_text(text):
    text = re.sub(r'[^\w\s]', '', text.encode('ascii', 'ignore').decode())
    text = re.sub(r'\d+', '', text).lower()
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    return ' '.join([w for w in tokens if w not in stop_words])

df['Clean_Text'] = df['text'].apply(clean_text)
df.drop(columns=['text'], inplace=True)

# -------------------------
# 3. Vector Store Preparation
# -------------------------
documents = [Document(page_content=f"id:{i}\nFillings: {row['Clean_Text']}\nFraud_Status: {row['fraud_status']}") for i, row in df.iterrows()]

embedding_model = HuggingFaceEmbeddings()
persist_dir = 'docs/chroma_rag/'
vectorstore = Chroma.from_documents(
    documents=documents,
    collection_name="finance_data_new",
    embedding=embedding_model,
    persist_directory=persist_dir
)

# -------------------------
# 4. Load LLM
# -------------------------
model_id = 'HuggingFaceH4/zephyr-7b-beta'
device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type='nf4',
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=bfloat16
)

model_config = AutoConfig.from_pretrained(model_id, trust_remote_code=True, max_new_tokens=1024)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    config=model_config,
    quantization_config=bnb_config,
    device_map='auto',
    trust_remote_code=True
)
tokenizer = AutoTokenizer.from_pretrained(model_id)

query_pipeline = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    torch_dtype=torch.float16,
    max_length=6000,
    max_new_tokens=500,
    device_map="auto"
)

llm = HuggingFacePipeline(pipeline=query_pipeline)

# -------------------------
# 5. RetrievalQA Setup
# -------------------------
PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["context", "query"],
    template="""
You are a Fraud Detection Expert in Financial Text Data. Analyze the given statement and predict if it's fraud or not.
If you don't know the answer, just say "Sorry, I Don't Know."
Question: {query}
Context: {context}
Answer:
"""
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 1})
qa_chain = RetrievalQA.from_chain_type(llm, retriever=retriever, chain_type_kwargs={"prompt": PROMPT_TEMPLATE})

# -------------------------
# 6. Run a Query
# -------------------------
query = "The company reported inflated revenues by including sales that never occurred."
try:
    result = qa_chain({"query": query})
    display(Markdown(f"**Question:** {query}\n\n**Answer:** {result['result']}"))
except RuntimeError as e:
    print(f"RuntimeError encountered: {e}")
