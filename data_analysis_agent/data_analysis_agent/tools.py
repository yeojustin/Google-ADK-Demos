import os
import google.auth
from typing import Optional, List
from pydantic import BaseModel, Field

from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.readonly_context import ReadonlyContext

from .prompt import ROOT_AGENT_INSTRUCTIONS

# --- 1. Schemas ---
class DataRow(BaseModel):
    label: str = Field(description="The category or x-axis value.")
    value: float = Field(description="The numerical or y-axis value.")

class ExtractedDataPayload(BaseModel):
    data: List[DataRow] = Field(description="The list of extracted data points.")
    summary: str = Field(description="Instructions for the visualizer on how to chart this.")

# --- 2. Custom Tools ---
def save_configuration(
    project_id: str,
    location: str = 'us-central1',
    tool_context: ToolContext = None
) -> str:
    """Save the BigQuery connection project in the session."""
    tool_context.state['project_id'] = project_id
    tool_context.state['location'] = location
        
    return f"Configuration saved: Project={project_id}, Loc={location}"

def save_data_for_visualizer(
    payload: ExtractedDataPayload,
    tool_context: ToolContext = None
) -> str:
    """CRITICAL HANDOFF TOOL: Pass the final extracted data to the visualizer."""
    tool_context.state['extracted_payload'] = payload.model_dump()
    return "Data successfully saved for the visualizer agent. You are done."


# --- 3. BigQuery Toolset Initialization ---
def setup_bq_toolset() -> BigQueryToolset:
    client_id = os.getenv('GOOGLE_CLIENT_ID') or os.getenv('OAUTH_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET') or os.getenv('OAUTH_CLIENT_SECRET')

    if client_id and client_secret:
        bq_credentials_config = BigQueryCredentialsConfig(
            client_id=client_id,
            client_secret=client_secret
        )
    else:
        # FIX: Removed the massive CredentialsWrapper. ADK accepts this natively.
        credentials, default_project_id = google.auth.default()
        bq_credentials_config = BigQueryCredentialsConfig(credentials=credentials)
        
    return BigQueryToolset(credentials_config=bq_credentials_config)

bigquery_toolset = setup_bq_toolset()

# --- 4. Agent Context ---

def get_root_agent_instruction(ctx: ReadonlyContext) -> str:
    auth_instruction = (
        "AUTHENTICATION NOTE:\n"
        "If you transfer to the Data Engineer and it encounters an 'Authorization Required' "
        "or 'Login' error when querying BigQuery, the system will natively provide the user "
        "with an auth link. Instruct the user to follow the link in their console/UI. "
        "Do not attempt to generate fake data."
    )
        
    return f"{ROOT_AGENT_INSTRUCTIONS}\n\n{auth_instruction}"