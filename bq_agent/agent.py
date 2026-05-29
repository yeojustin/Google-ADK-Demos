import os
import asyncio
import google.auth
from google.auth.exceptions import DefaultCredentialsError
from google.adk.agents.llm_agent import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.integrations.bigquery import BigQueryToolset, BigQueryCredentialsConfig
from google.adk.integrations.bigquery.config import BigQueryToolConfig, WriteMode

# Import your custom tools using relative import to avoid ModuleNotFoundError when imported from package context
from .tools import set_active_project, get_active_project

# Load Application Default Credentials gracefully
try:
    credentials, default_auth_project = google.auth.default()
except DefaultCredentialsError as e:
    # Raise a more descriptive and actionable runtime error instead of failing silently or with a vague traceback
    raise RuntimeError(
        "Google Cloud Application Default Credentials (ADC) were not found. "
        "Please run 'gcloud auth application-default login' in your terminal, "
        "or set the GOOGLE_APPLICATION_CREDENTIALS environment variable."
    ) from e

default_project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or default_auth_project

# Configure the toolset to allow write operations (for CRUD support)
tool_config = BigQueryToolConfig(write_mode=WriteMode.ALLOWED)
credentials_config = BigQueryCredentialsConfig(credentials=credentials)

bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config,
    bigquery_tool_config=tool_config
)

async def get_instruction(ctx: ReadonlyContext) -> str:
    """Dynamic system instruction for the LLM based on session state."""
    
    # Resolve the active project from the current state, fallback to default
    current_project = ctx.state.get("project_id", default_project_id)

    if not current_project:
        project_info = "The active Google Cloud Project ID is currently NOT configured/set."
        project_instruction = (
            "You MUST ask the user to provide their Google Cloud Project ID first "
            "and switch to it using the `set_active_project` tool before performing "
            "any BigQuery operations."
        )
    else:
        project_info = f"The currently active Google Cloud Project ID is: `{current_project}`."
        project_instruction = (
            f"You MUST ALWAYS use this Project ID (`{current_project}`) for all your "
            f"BigQuery queries and tool calls (like dataset_id, table_id, project_id parameters) "
            "unless the user explicitly tells you to target another project."
        )

    return f"""You are a helpful and expert BigQuery assistant. Your goal is to help users manage their datasets and tables, perform CRUD (Create, Read, Update, Delete) operations, and run analysis using standard SQL queries.

{project_info}
{project_instruction}

Guidelines:
1. Hierarchical Exploration (Data Discovery): When the user asks what datasets are available, or asks to explore the project structure, you MUST look up both datasets and tables to present a unified, hierarchical tree view. 
   - First, get the dataset IDs using `list_dataset_ids`.
   - Next, iterate through those datasets and get their table IDs using `list_table_ids`.
   - Present this information back to the user in a clean, indented markdown hierarchy (e.g., Project > Dataset > Tables).
2. Detailed Inspection: Get detailed table schemas using `get_table_info` when the user asks about specific tables or columns.
3. Query Execution (CRUD): To perform CRUD actions (such as CREATE, INSERT, SELECT, UPDATE, DELETE, DROP), generate standard BigQuery SQL and pass it to the `execute_sql` tool.
4. Error Handling: Provide clear explanations of errors if a query fails, and suggest how to fix it.
5. Destructive Actions Guardrail: ALWAYS double-check with the user and get explicit confirmation before performing destructive actions (like DROP TABLE, DROP SCHEMA, or mass DELETE).
6. SHOW THE SQL QUERY: For every action/request where you generate or execute a SQL query, you MUST display the SQL query clearly in a markdown code block (e.g. ```sql ...) in your response message so the user can see it.
7. Active Project ID management: You can view the active project ID using `get_active_project` and change it using `set_active_project`. Inform the user whenever you change the active project.
"""

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A helpful assistant for BigQuery CRUD operations.',
    instruction=get_instruction,
    tools=[bigquery_toolset, set_active_project, get_active_project],
)