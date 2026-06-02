import os
from pydantic import BaseModel, Field
from typing import List
from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.tool_context import ToolContext
import google.auth

# 1. State Schema
class ExtractedDataPayload(BaseModel):
    summary: str = Field(description="Summary of the extracted data.")

# 2. Handoff Tool
def save_data_for_visualizer(payload: ExtractedDataPayload, tool_context: ToolContext = None) -> str:
    """Saves extracted data to shared state for the visualizer."""
    tool_context.state['extracted_payload'] = payload.model_dump()
    return "Data saved for visualizer."

# 3. Native BQ Toolset
credentials, _ = google.auth.default()
bigquery_toolset = BigQueryToolset(
    credentials_config=BigQueryCredentialsConfig(credentials=credentials)
)