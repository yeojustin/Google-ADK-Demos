import os
from google.adk.agents import LlmAgent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools import AgentTool # <-- IMPORT AGENTTOOL

from .prompt import DATA_ENGINEER_INSTRUCTIONS, VISUALISER_INSTRUCTIONS
from .tools import (
    bigquery_toolset,
    save_configuration,
    save_data_for_visualizer,
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

# FIX: Wrap the sub-agents in AgentTool to mask the Code Executor from the API
data_engineer_tool = AgentTool(agent=data_engineer_agent)
visualiser_tool = AgentTool(agent=visualiser_agent)

root_agent = LlmAgent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='A coordinator that delegates data engineering and visualization tasks.',
    instruction=get_root_agent_instruction,
    # FIX: Pass the AgentTools as standard tools. DO NOT use sub_agents=[] here.
    tools=[save_configuration, data_engineer_tool, visualiser_tool]
)