from google.adk.agents.llm_agent import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService 
from google.adk.tools.tool_context import ToolContext
from pathlib import Path
from google.adk.tools import FunctionTool
import google.genai.types as types
from google.adk.agents.callback_context import CallbackContext


# Mock tool implementation
def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}

async def save_generated_report_py(tool_context: ToolContext, file: str):
    """Saves any file as an artifact."""
    print(f"Saving file.")
    report_artifact = types.Part.from_text(
        text=file
    )
    filename = "generated_report.pdf"

    try:
        await tool_context.save_artifact(filename=filename, artifact=report_artifact)
        print(f"Successfully saved Python artifact '{filename}'.")
        # The event generated after this callback will contain:
        # event.actions.artifact_delta == {"generated_report.pdf": version}
    except ValueError as e:
        print(f"Error saving Python artifact: {e}. Is ArtifactService configured in Runner?")
    except Exception as e:
        # Handle potential storage errors (e.g., GCS permissions)
        print(f"An unexpected error occurred during Python artifact save: {e}")

async def list_user_files_py(tool_context: ToolContext) -> str:
    """Tool to list available artifacts for the user."""
    try:
        available_files = await tool_context.list_artifacts()
        if not available_files:
            return "You have no saved artifacts."
        else:
            # Format the list for the user/LLM
            file_list_str = "\n".join([f"- {fname}" for fname in available_files])
            return f"Here are your available Python artifacts:\n{file_list_str}"
    except ValueError as e:
        print(f"Error listing Python artifacts: {e}. Is ArtifactService configured?")
        return "Error: Could not list Python artifacts."
    except Exception as e:
        print(f"An unexpected error occurred during Python artifact list: {e}")
        return "Error: An unexpected error occurred while listing Python artifacts."

artifact_service = InMemoryArtifactService() # Choose an implementation
session_service = InMemorySessionService()

list_files_tool = FunctionTool(func=list_user_files_py)
save_files_tool = FunctionTool(func=save_generated_report_py)


"""root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="Data analyst.",
    instruction=
        You are an expert scrapping and extracting data from screenshots (images). 
        So once an image is received, you have to generate a visual diagram.
        
        Take into account this to generate the diagram:

        - Available subsystems are Payment Service and IBE (which does the requests)
    ,
    tools=[list_files_tool]
)"""

root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description="Artifact manager",
    instruction="You are the artifact manager. Anything you receive assume it must be saved (if it's not explicitly said to do something else).",
    tools=[list_files_tool, save_files_tool]
)

runner = Runner(
    agent=root_agent,
    app_name="agents",
    session_service=session_service,
    artifact_service=artifact_service # Provide the service instance here
)
