import os
from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor

from .prompt import DATA_ENGINEER_INSTRUCTIONS, VISUALISER_INSTRUCTIONS
from .tools import (
    bigquery_toolset,
    save_configuration,
    save_data_for_visualizer,
    request_credentials,
    get_root_agent_instruction
)

# --- 4. Agent Definitions ---

data_engineer_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='data_engineer_agent',
    description='Queries BigQuery and extracts the requested data.',
    instruction=DATA_ENGINEER_INSTRUCTIONS,
    tools=[bigquery_toolset, save_data_for_visualizer]
)

visualiser_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='visualizer',
    description='Reads data from state and writes Python code to visualize it.',
    instruction=VISUALISER_INSTRUCTIONS,
    code_executor=BuiltInCodeExecutor() 
)

# --- 5. Workflow Orchestration ---
root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A coordinator that delegates data engineering and visualization tasks.',
    instruction=get_root_agent_instruction,
    tools=[save_configuration, request_credentials],
    sub_agents=[data_engineer_agent, visualiser_agent]
)