from pathlib import Path  # working with filesystem paths for search/delete tools
ROOT_DIR = Path(__file__).parent.resolve()  # The coding_assistant folder

#-------standard library imports: general python features, used across all exercises
from os import getenv
import asyncio
from typing import Any, Callable
from dataclasses import dataclass
import subprocess
import os
ROOT_DIR = Path(__file__).parent.resolve()  # The coding_assistant folder

#-------standard library imports: general python features, used across all exercises
from os import getenv # function that reads API_KEY
import asyncio #framework to wait for OpenAI/OpenRouter response and don’t block everything else
from typing import Any, Callable #read any type, call a function onn a value
from dataclasses import dataclass #create classes to store data, creates __init__, etc
import subprocess  # For running external commands like opening files in VS Code
import os  # For interacting with the operating system, e.g., checking file existence

#-------third-party imports: libraries installed via pip
from dotenv import load_dotenv #load .env into the environment
from rich.console import Console #"nicer" replacement for print

#-------pydantic AI: interact with LLMs, define agent's capabilities, tools, and run the agent
from pydantic_ai.providers.openai import OpenAIProvider #how to talk to the OpenAI API server
from pydantic_ai.models.openai import OpenAIResponsesModel #which model on that server, and in what format
from pydantic_ai import Agent, RunContext, ModelSettings #runs agent, model's behaviour

#-------pydantic AI extensions: capabilities, toolsets, tool call types
from pydantic_ai.capabilities import AbstractCapability #defining capabiloities of our agent
from pydantic_ai.toolsets import FunctionToolset, AgentToolset #container of tools, and a toolset for the agent
from pydantic_ai.tools import ToolCallPart, ToolDefinition #tool call and tool definition for the agent

from skills import Skills # skills capability, telling the agent which skills exist
# Load environment variables from .env file

#global setup: loading the API key and defining of the "Dependencies container"
load_dotenv()

@dataclass
class AgentDeps:
    console: Console

# Helper function to validate paths
def is_within_root(path: Path) -> bool:
    """Check if the given path is within the root directory."""
    try:
        # Resolve the path and check if it starts with the root directory
        return ROOT_DIR in path.resolve().parents or path.resolve() == ROOT_DIR
    except Exception:
        return False

# Step 1: Configuring a provider & model
provider = OpenAIProvider(
    base_url = "https://openrouter.ai/api/v1",
    api_key = getenv("API_KEY")
)

model = OpenAIResponsesModel(
    model_name = "gpt-5.1-codex-mini",
    provider = provider,
)

# Step 2: defining file tools & capabilities - exercise 3
file_toolset = FunctionToolset() # Create an empty toolset to hold our file tools

#defining a function that knows how to read and write the file
def read_file(path: str) -> str:
    """
    Open a text file within the project root in VS Code.

    Parameters:
        path: Path to the file, relative to the project root (e.g. "skills/skills.py").

    Returns:
        A short confirmation message with the resolved relative path.
    """
    # Start with the path relative to the project root
    file_path = ROOT_DIR / path

    # Enforce sandbox: path must be within ROOT_DIR
    if not is_within_root(file_path):
        raise PermissionError(
            f"Access denied: '{file_path}' is outside the root directory."
        )

    # If the file doesn't exist at that exact path, search inside ROOT_DIR
    if not file_path.exists():
        matches = list(ROOT_DIR.rglob(path))
        if not matches:
            raise FileNotFoundError(
                f"File '{path}' not found in the root directory."
            )
        if len(matches) > 1:
            raise FileNotFoundError(
                "Multiple files named "
                f"'{path}' found. Please specify the folder:\n"
                + "\n".join(str(match.relative_to(ROOT_DIR)) for match in matches)
            )
        file_path = matches[0]

    # Open the file in VS Code using the 'code' CLI
    subprocess.run(["code", str(file_path)], check=False)

    return f"Opened {file_path.relative_to(ROOT_DIR)} in the editor."

def write_file(path: str, content: str) -> str:
    """
    Write text content to a UTF-8 file within the project root, overwriting if it exists.

    Parameters:
        path: Path to the file to write, relative to the project root.
        content: Text content to write.

    Returns:
        A short confirmation message about what was written.
    """
    file_path = ROOT_DIR / path

    # Enforce sandbox: path must be within ROOT_DIR
    if not is_within_root(file_path):
        raise PermissionError(
            f"Access denied: '{file_path}' is outside the root directory."
        )

    # Ensure the parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as our_file:
        our_file.write(content)

    return f"Wrote {len(content)} characters to '{file_path.relative_to(ROOT_DIR)}'."

def search_files(pattern: str) -> list[str]:
    """
    Search for files and folders matching a glob pattern under the project root.

    Parameters:
        pattern:
            A glob-style pattern like "*.py", "tests/test_*.py", or "**/*.md".

    Returns:
        A sorted list of matching paths as strings, relative to the project root.
    """
    matches = [
        str(path.relative_to(ROOT_DIR))
        for path in ROOT_DIR.rglob(pattern)
    ]
    return sorted(matches)

def delete_file(path: str) -> str:
    """
    Delete a file from disk.

    Parameters:
        path:
            Path to the file to delete.

    Returns:
        A short confirmation or error message.
    """
    file_path = ROOT_DIR / path
    
    # Validate the file path
    if not is_within_root(file_path):
        raise PermissionError(f"Access denied: '{file_path}' is outside the root directory.")

    if not file_path.exists():
        return f"No file found at '{file_path.relative_to(ROOT_DIR)}'."

    if file_path.is_dir():
        return f"'{file_path.relative_to(ROOT_DIR)}' is a directory, not a file. Refusing to delete."

    # Ask for user confirmation
    confirmation = input(f"Are you sure you want to delete '{file_path.relative_to(ROOT_DIR)}'? (yes/no): ").strip().lower()
    if confirmation not in {"yes", "y"}:
        return f"Deletion of '{file_path.relative_to(ROOT_DIR)}' canceled."

    # Proceed with deletion
    file_path.unlink()
    return f"Deleted '{file_path.relative_to(ROOT_DIR)}'."

def create_folder(path: str) -> str:
    """Create a new folder within the root directory."""
    folder_path = ROOT_DIR / path  # Ensure the path is relative to the root directory

    # Validate the folder path
    if not is_within_root(folder_path):
        raise PermissionError(f"Access denied: '{folder_path}' is outside the root directory.")

    # Create the folder
    try:
        folder_path.mkdir(parents=True, exist_ok=False)
        return f"Folder '{folder_path.relative_to(ROOT_DIR)}' created successfully."
    except FileExistsError:
        return f"Folder '{folder_path.relative_to(ROOT_DIR)}' already exists."

def move_file(source: str, destination: str) -> str:
    """Move a file from one folder to another within the root directory."""
    source_path = ROOT_DIR / source  # Ensure the source path is relative to the root directory
    
    destination_path = ROOT_DIR / destination  # Ensure the destination path is relative to the root directory

# Validate the source and destination paths
    if not is_within_root(source_path) or not is_within_root(destination_path):
        raise PermissionError("Access denied: Source or destination is outside the root directory.")

    if not source_path.exists():
        raise FileNotFoundError(f"Source file '{source_path.relative_to(ROOT_DIR)}' does not exist.")

    if destination_path.is_dir():
        destination_path = destination_path / source_path.name  # Append the file name to the destination folder

    # Move the file
    try:
        source_path.rename(destination_path)
        return f"Moved '{source_path.relative_to(ROOT_DIR)}' to '{destination_path.relative_to(ROOT_DIR)}'."
    except Exception as e:
        return f"Failed to move file: {e}"

# registering the functions on file_toolset - exersice 3
file_toolset.add_function(read_file)
file_toolset.add_function(write_file)
file_toolset.add_function(search_files)
file_toolset.add_function(delete_file)
file_toolset.add_function(create_folder)
file_toolset.add_function(move_file)

class FileOperations(AbstractCapability[Any]):
    """
    Capability exposing basic file operations (read_file, write_file)
    as tools the agent can call.
    """

    def get_toolset(self) -> AgentToolset[Any] | None:
        return file_toolset


# Step 3: hook to log tool calls - for Exercise 4
    async def before_tool_execute(
        self,
        ctx: RunContext[AgentDeps],
        *,
        call: ToolCallPart,
        tool_def: ToolDefinition,
        args: dict[str, Any],
    ) -> dict[str, Any]:
        ctx.deps.console.print(f"[cyan]Calling tool:[/cyan] {call.tool_name}")
        return args

#ReasoningEffort capability (same indent as FileOperations, i.e. top level)
class ReasoningEffort(AbstractCapability[Any]):
    """
    Dynamically choose reasoning effort: 'low', 'medium', or 'high'
    based on the original user prompt.
    """
    def get_model_settings(self) -> Callable[[RunContext[Any]], ModelSettings]:
        def _set_reasoning_effort(ctx: RunContext[Any]) -> ModelSettings:
            prompt = (ctx.prompt or "").lower()

            if len(prompt) < 40 or any(
                word in prompt for word in ("quick", "short", "simple", "example")
            ):
                effort = "low"
            elif any(
                word in prompt
                for word in ("complex", "difficult", "optimize", "debug", "analyze")
            ):
                effort = "high"
            else:
                effort = "medium"
            
            return ModelSettings(thinking = effort)

        return _set_reasoning_effort


# Step 4: Agent and g everything together
agent = Agent(
    model = model,
    instructions = ''' You are a Python coding agent. Write clear, correct, and minimal Python code.

You also have tools to work with the project files:

- search_files(pattern): search under the project root.
- read_file(path): open a file in the editor.
- write_file(path, content): write text to a file.
- delete_file(path): delete a file.
- create_folder(path): create a folder under the project root.
- move_file(source, destination): move a file from source to destination under the project root.

When the user asks you to move or rename files, you MUST use move_file,
once for each file, and confirm the final locations using search_files if helpful.
All paths are relative to the project root. ''',
    capabilities = [FileOperations(), ReasoningEffort(), Skills()],
    deps_type = AgentDeps,
)

# Steps 5: Conversation loop where we chat with the agent
async def main() -> None:
    console = Console()
    deps = AgentDeps(console = console)
    
    message_history = None 
    while True: 
        console.print("[yellow]Your question: [/yellow]", end = "")
        user_input = input()
        
        if user_input.strip().lower() in {"exit", "quit"}:
            break
        
        result = await agent.run(
            user_input, 
            message_history = message_history, 
            deps = deps,
            )
        
        print() #Blank line between question and answer
        
        console.print("[green]Assistant: [/green]", end = "")
        print(result.output)
        
        print() #extra blank line before the next question
        
        message_history = result.all_messages()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")

