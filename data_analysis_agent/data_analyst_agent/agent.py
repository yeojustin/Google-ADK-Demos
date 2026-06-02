import google.auth
from google.adk.agents.llm_agent import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.bigquery import (
    BigQueryToolset,
    BigQueryCredentialsConfig
)
from google.adk.tools.bigquery.config import (
    BigQueryToolConfig,
    WriteMode
)

# Automatically get credentials from the gcloud environment
application_default_credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(
    credentials=application_default_credentials
)

# Configure the BigQuery tool
tool_config = BigQueryToolConfig(
    write_mode=WriteMode.ALLOWED,
    application_name='data_analyst_agent'
)

# Create the toolset with the specified configurations
bigquery_toolset = BigQueryToolset(
    credentials_config=credentials_config, bigquery_tool_config=tool_config
)

# Create an agent with google search tool as a search specialist
google_search_agent = Agent(
    model='gemini-2.5-flash',
    name='google_search_agent',
    description='A search agent that uses google search to get latest information about current events, weather, or business hours.',
    instruction='Use google search to answer user questions about real-time, logistical information.',
    tools=[google_search],
)

# Define the final agent with its instructions and tools
root_agent = Agent(
    model="gemini-2.5-flash",
    name="bigquery_agent",
    description=(
        "Agent to answer questions about BigQuery data and execute SQL queries."
    ),
    instruction="""
        You are an expert data analyst agent with access to BigQuery tools.
        When a user asks about a dataset, first use your tools to understand its schema.
        Then, use this knowledge to construct and execute SQL queries to answer the user's questions.
        Always confirm with the user if their question is ambiguous (e.g., for which year?).
    """,
    tools=[
        AgentTool(google_search_agent),
        bigquery_toolset
    ],
)