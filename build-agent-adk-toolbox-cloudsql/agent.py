import os
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams

# Load environment variables from .env file
load_dotenv()

# 1. Configure the connection parameters to the local MCP toolbox server
# Note: Using port 5001 as configured for macOS compatibility
connection_params = SseConnectionParams(
    url="http://localhost:5001/mcp/sse"
)

# 2. Initialize the MCP Toolset
# This automatically fetches the database tools from the toolbox server
mcp_toolset = McpToolset(connection_params=connection_params)

# 3. Create the agent and attach the MCP toolset
root_agent = Agent(
    model="gemini-2.5-flash",
    name="restaurant_agent",
    description="A restaurant assistant to help browse dishes, category details, or search descriptions.",
    instruction="""
        You are a helpful restaurant assistant.
        Use your tools to find menu items, category details, or search by descriptions.
        Always explain the dish details including price and availability to the user.
    """,
    tools=[mcp_toolset]
)
