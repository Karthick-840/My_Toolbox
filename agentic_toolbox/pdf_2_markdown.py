import nest_asyncio

nest_asyncio.apply()

import os

os.environ["LLAMA_CLOUD_API_KEY"] = "llx-wpg3hV3pm4ZbrBrXtpQ0bIEZe1IaNwgkfzqCUdIrVKjsUbLs"



from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()
response = query_engine.query("Some question about the data should go here")
print(response)

# document = LlamaParse(result_type="markdown").load_data("apple_10k.pdf")

# file_name = "apple_10k.md"
# with open(file_name, 'w') as file:
#     file.write(document[0].text)
from llama_parse import LlamaParse
documents_with_instruction = LlamaParse(
    result_type="markdown",
    parsing_instruction="""
    This is the Apple anual report.
    """
    ).load_data("apple_10k.pdf")


file_name = "apple_10k_instructions.md"
with open(file_name, 'w') as file:
    file.write(documents_with_instruction[0].text)


import nest_asyncio

nest_asyncio.apply()

from llama_parse import LlamaParse

parser = LlamaParse(
    api_key="llx-...",  # can also be set in your env as LLAMA_CLOUD_API_KEY
    result_type="markdown",  # "markdown" and "text" are available
    num_workers=4,  # if multiple files passed, split in `num_workers` API calls
    verbose=True,
    language="en",  # Optionally you can define a language, default=en
)

# sync
documents = parser.load_data("./my_file.pdf")

# sync batch
documents = parser.load_data(["./my_file1.pdf", "./my_file2.pdf"])

# async
documents = await parser.aload_data("./my_file.pdf")

# async batch
documents = await parser.aload_data(["./my_file1.pdf", "./my_file2.pdf"])


import nest_asyncio

nest_asyncio.apply()

from llama_parse import LlamaParse

parser = LlamaParse(
    api_key="llx-...",  # can also be set in your env as LLAMA_CLOUD_API_KEY
    result_type="markdown",  # "markdown" and "text" are available
    num_workers=4,  # if multiple files passed, split in `num_workers` API calls
    verbose=True,
    language="en",  # Optionally you can define a language, default=en
)

file_name = "my_file1.pdf"
extra_info = {"file_name": file_name}

with open(f"./{file_name}", "rb") as f:
    # must provide extra_info with file_name key with passing file object
    documents = parser.load_data(f, extra_info=extra_info)

# you can also pass file bytes directly
with open(f"./{file_name}", "rb") as f:
    file_bytes = f.read()
    # must provide extra_info with file_name key with passing file bytes
    documents = parser.load_data(file_bytes, extra_info=extra_info)


import nest_asyncio

nest_asyncio.apply()

from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader

parser = LlamaParse(
    api_key="llx-...",  # can also be set in your env as LLAMA_CLOUD_API_KEY
    result_type="markdown",  # "markdown" and "text" are available
    verbose=True,
)

file_extractor = {".pdf": parser}
documents = SimpleDirectoryReader(
    "./data", file_extractor=file_extractor
).load_data()

"https://github.com/run-llama/llama_parse.git"