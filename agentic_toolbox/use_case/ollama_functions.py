import json
from typing import Optional, Type
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_experimental.llms.ollama_functions import OllamaFunctions


class OllamaLangClient:
    def __init__(self, model: str = "llama3", temperature: float = 0.1, format: str = "json"):
        self.llm = OllamaFunctions(
            model=model,
            format=format,
            temperature=temperature,
            keep_alive=-1,
        )

    def call_with_tool(
        self,
        query: str,
        tool_schema: dict,
        tool_name: str = "get_tool",
        tool_description: str = "Generic tool call",
        function_call: Optional[dict] = None,
    ):
        model = self.llm.bind_tools(
            tools=[
                {
                    "name": tool_name,
                    "description": tool_description,
                    "parameters": tool_schema,
                }
            ],
            function_call=function_call or {"name": tool_name},
        )
        return model.invoke(query)

    def call_with_schema(self, schema: dict, user_input: str) -> dict:
        prompt = ChatPromptTemplate.from_messages([
            HumanMessage(content="Please follow the JSON schema below to format your response:"),
            HumanMessage(content="{schema}"),
            HumanMessage(content=user_input),
        ])
        dumps = json.dumps(schema, indent=2)
        chain = prompt | self.llm | JsonOutputParser()
        return chain.invoke({"schema": dumps})

    def call_with_pydantic(self, question: str, context: str, schema_class: Type[BaseModel], prompt_template: Optional[str] = None):
        structured_llm = self.llm.with_structured_output(schema_class)

        prompt_template = prompt_template or (
            """<|user|>{context}\n\nQUESTION: {question}<|end|>\n<|assistant|>AI: """
        )
        prompt = PromptTemplate.from_template(prompt_template)

        chain = prompt | structured_llm
        return chain.invoke({"question": question, "context": context})


from pydantic import BaseModel, Field
from ollama_client import OllamaLangClient

client = OllamaLangClient(model="phi3")

# TOOL CALLING EXAMPLE
weather_schema = {
    "type": "object",
    "properties": {
        "location": {"type": "string", "description": "City and state"},
        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
    },
    "required": ["location"]
}

response = client.call_with_tool(
    query="What is the weather in Singapore?",
    tool_schema=weather_schema,
    tool_name="get_current_weather",
    tool_description="Get current weather data"
)

print("Tool Response:", response)

# STRUCTURED OUTPUT WITH PYDANTIC
class Person(BaseModel):
    name: str = Field(description="The person's name", required=True)
    height: float = Field(description="The person's height", required=True)
    hair_color: str = Field(description="The person's hair color")

context = """Alex is 5 feet tall. 
Claudia is 1 feet taller than Alex. Claudia is brunette. Alex is blonde."""

response = client.call_with_pydantic(
    question="Who is taller?",
    context=context,
    schema_class=Person,
)

print("Structured Pydantic Response:", response)
