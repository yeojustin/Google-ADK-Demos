import os
import google.auth
import google.auth.credentials
from typing import Optional, List
from pydantic import BaseModel, Field

from google.adk.tools.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, OAuth2Auth
from google.adk.auth.auth_tool import AuthConfig
from fastapi.openapi.models import OAuth2, OAuthFlows, OAuthFlowAuthorizationCode

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
    dataset_id: str,
    location: str = 'us-central1',
    tool_context: ToolContext = None
) -> str:
    """Save the BigQuery connection and credentials in the session."""
    tool_context.state['project_id'] = project_id
    tool_context.state['dataset_id'] = dataset_id
    tool_context.state['location'] = location
        
    return f"Configuration saved: Project={project_id}, Dataset={dataset_id}, Loc={location}"

def save_data_for_visualizer(
    payload: ExtractedDataPayload,
    tool_context: ToolContext = None
) -> str:
    """CRITICAL HANDOFF TOOL: Pass the final extracted data to the visualizer."""
    tool_context.state['extracted_payload'] = payload.model_dump()
    return "Data successfully saved for the visualizer agent. You are done."

def request_credentials(tool_context: ToolContext = None) -> str:
    """Request Google OAuth credentials from the user to authorize BigQuery access."""
    client_id = os.getenv('GOOGLE_CLIENT_ID') or os.getenv('OAUTH_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET') or os.getenv('OAUTH_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        return (
            "Using local Application Default Credentials (ADC) for authentication. "
            "No interactive sign-in flow is needed."
        )
        
    auth_scheme = OAuth2(
        flows=OAuthFlows(
            authorizationCode=OAuthFlowAuthorizationCode(
                authorizationUrl="https://accounts.google.com/o/oauth2/auth",
                tokenUrl="https://oauth2.googleapis.com/token",
                scopes={
                    "https://www.googleapis.com/auth/bigquery": "Access to BigQuery"
                },
            )
        )
    )

    auth_credential = AuthCredential(
        auth_type=AuthCredentialTypes.OAUTH2,
        oauth2=OAuth2Auth(
            client_id=client_id,
            client_secret=client_secret,
        ),
    )

    tool_context.request_credential(
        AuthConfig(
            auth_scheme=auth_scheme,
            raw_auth_credential=auth_credential,
        )
    )
    return "Google Authentication popup has been triggered. Please authorize access in the browser."

# --- 3. BigQuery Toolset Initialization ---
# ADK Best Practice: Let the Config handle the credentials cleanly.

def setup_bq_toolset() -> BigQueryToolset:
    client_id = os.getenv('GOOGLE_CLIENT_ID') or os.getenv('OAUTH_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET') or os.getenv('OAUTH_CLIENT_SECRET')

    if client_id and client_secret:
        bq_credentials_config = BigQueryCredentialsConfig(
            client_id=client_id,
            client_secret=client_secret
        )
    else:
        raw_credentials, default_project_id = google.auth.default()

        class CredentialsWrapper(google.auth.credentials.Credentials):
            def __init__(self, target):
                super().__init__()
                self._target = target

            def __getattr__(self, name):
                return getattr(self._target, name)

            @property
            def valid(self):
                return self._target.valid

            @property
            def expired(self):
                return self._target.expired

            @property
            def token(self):
                return getattr(self._target, 'token', None)

            def refresh(self, request):
                if hasattr(self._target, 'refresh'):
                    try:
                        self._target.refresh(request)
                    except Exception:
                        pass

        credentials = CredentialsWrapper(raw_credentials)
        bq_credentials_config = BigQueryCredentialsConfig(credentials=credentials)
        
    return BigQueryToolset(credentials_config=bq_credentials_config)

bigquery_toolset = setup_bq_toolset()

# --- 4. Agent Context ---

def get_root_agent_instruction(ctx: ReadonlyContext) -> str:
    """
    Dynamically construct the root instruction without snooping internal cache keys.
    Instead, instruct the agent to gracefully handle authorization errors if they occur.
    """
    auth_instruction = (
        "AUTHENTICATION NOTE:\n"
        "If you encounter an 'Authorization Required' or 'Login' error when using BigQuery tools, "
        "or if you see that authentication is needed, call the `request_credentials` tool "
        "to trigger the interactive sign-in flow for the user. Do not try to generate fake data; "
        "wait for the user to confirm they have logged in."
    )
        
    return f"{ROOT_AGENT_INSTRUCTIONS}\n\n{auth_instruction}"