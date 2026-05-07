from praisonaiagents import Agent, MCP



search_agent = Agent(instructions = """ You help book apartmetns on AirBnB""",
                     llm = "ollama/llama3.2",
                     tools = MCP("npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt"))


search_agent.start("Search for apartmetns in dubai for 2 nights for 18th April 2025 to 20th april 2025 " \
"with prices below 20 euro per night for 1 person and preeferably close to dubai marina witha  ncie view. give me 4 suggestions and provide their links")

# https://github.com/modelcontextprotocol/servers?tab=readme-ov-file

# C:\Users\gksme\OneDrive - Bayer\Personal Data\Local_Git_Projects\profile\LLM\Autogen_AI_Agent_Toolbox\AgenticAI_AIAgents_Course\GenAI_DeepSeek_AI_Agent\chroma_db\39893732-012d-4c0d-a1fb-43f12818dcab