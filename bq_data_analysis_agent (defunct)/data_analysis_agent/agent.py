import google.auth
from pydantic import BaseModel, Field
from typing import List

from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.tool_context import ToolContext
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool
from google.adk.code_executors import BuiltInCodeExecutor

# ==========================================
# 1. TOOLS, SCHEMA & STATE
# ==========================================
credentials, _ = google.auth.default()
bq_toolset = BigQueryToolset(credentials_config=BigQueryCredentialsConfig(credentials=credentials))

# --- STRICT PYDANTIC CONTRACT ---
class DataPoint(BaseModel):
    label: str = Field(description="The category, name, or x-axis value (e.g., Year, State).")
    value: float = Field(description="The numerical or y-axis value (e.g., Total, Count).")

class ExtractedDataPayload(BaseModel):
    summary: str = Field(description="Summary of what this data represents.")
    data_points: List[DataPoint] = Field(description="The strictly formatted data rows.")

def save_data(payload: ExtractedDataPayload, tool_context: ToolContext = None) -> str:
    """Saves strictly validated data to shared state for the visualizer to use."""
    tool_context.state['data'] = payload.model_dump()
    return "Data saved in strict format for the visualizer."

# ==========================================
# 2. SUB-AGENTS (The Workers)
# ==========================================
engineer = LlmAgent(
    name="engineer",
    model="gemini-2.5-flash",
    tools=[bq_toolset, save_data],
    instruction="""You are a backend Data Engineer. You only execute tools.
    1. DISCOVERY: If asked to list tables, first list datasets, read the output, then list the tables for those datasets. 
    2. EXTRACTION: If asked to query data, write the SQL, execute it, and format the results exactly into the `save_data` tool schema.
    3. TRANSPARENCY: Always show your exact SQL in a ```sql block."""
)

visualizer = LlmAgent(
    name="visualizer",
    model="gemini-2.5-flash",
    code_executor=BuiltInCodeExecutor(),
    instruction="""You are a Python Visualizer.
    1. Read the structured data from session state: {data?}
    2. Write Python (pandas/matplotlib) to chart the `data_points` array and save it to "chart.png".
    3. Output your Python code in a ```python block."""
)

# ==========================================
# 3. ROOT COORDINATOR (The Hub)
# ==========================================
root_agent = LlmAgent(
    name="coordinator",
    model="gemini-2.5-flash",
    tools=[AgentTool(agent=engineer), AgentTool(agent=visualizer)],
    instruction="""You coordinate the workflow.
    1. If the user gives a Project ID, immediately call the `engineer` tool: "List all datasets and tables for project ID: [ID]."
    2. Present the tables to the user and ask what they want to query.
    3. To query data, explicitly pass the project ID and request to the `engineer` tool.
    4. To visualize data, call the `visualizer` tool.
    Always ask the user for next steps."""
)