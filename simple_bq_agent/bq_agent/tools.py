from google.adk.tools.tool_context import ToolContext

def set_active_project(project_id: str, tool_context: ToolContext) -> str:
    """Set the active Google Cloud project ID in the session state.

    Args:
        project_id: The new Google Cloud project ID to set as active.
    """
    tool_context.state["project_id"] = project_id
    return f"Successfully switched active project to: {project_id}"


def get_active_project(tool_context: ToolContext) -> str:
    """Retrieve the currently active Google Cloud project ID from session state."""
    active_project = tool_context.state.get("project_id")
    if not active_project:
        return "No active project ID set in session state."
    return f"Active project ID: {active_project}"