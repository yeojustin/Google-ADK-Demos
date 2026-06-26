import os
import sys
import warnings

# Suppress experimental/deprecation warnings to keep output clean
warnings.filterwarnings("ignore")

# Force using Vertex AI backend (which uses Application Default Credentials)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from agent import root_agent

def main():
    print("Initializing ADK Runner and connecting to local MCP server...")
    
    # 1. Create the InMemoryRunner using the agent defined in agent.py
    runner = InMemoryRunner(root_agent)
    
    # 2. Pre-create the session for testing
    user_id = "test_user"
    session_id = "test_session"
    runner.session_service.create_session_sync(
        app_name="InMemoryRunner",
        user_id=user_id,
        session_id=session_id
    )
    
    # 3. Prompt user for query or use default
    query = "What Italian dishes do you have?"
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        
    print(f"\nUser: {query}")
    print("Agent responding...\n")
    
    # 4. Construct the query payload
    content = Content(parts=[Part.from_text(text=query)])
    
    # 5. Run the agent and extract clean text output from events
    for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(part.text, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    main()
