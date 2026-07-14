#-------standard library imports: general python features, used across all exercises
from os import getenv # function that reads API_KEY
import asyncio #framework to wait for OpenAI/OpenRouter response and don’t block everything else
from typing import Any, Callable #read any type, call a function onn a value
from dataclasses import dataclass #create classes to store data, creates __init__, etc
from pathlib import Path  # working with filesystem paths for search/delete tools

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
    """ Read a UTF-8 text file from disk and return its contents as a string.

    Parameters:
        path: Path to the file to read.

    Returns:
        The text contents of the file.
    """
    with open(path, "r", encoding = "utf-8") as our_file:
        return our_file.read()

def write_file(path: str, content: str) -> str:
    """
    Write text content to a UTF-8 file on disk, overwriting if it exists.

    Parameters:
        path: Path to the file to write.
        content: Text content to write.

    Returns:
        A short confirmation message about what was written.
    """
    with open(path, "w", encoding = "utf-8") as our_file:
        our_file.write(content)
    return f"Wrote {len(content)} characters to '{path}'."

def search_files(pattern: str, root: str = ".") -> list[str]:
    """
    Search for files matching a glob pattern under a root directory.

    Parameters:
        pattern:
            A glob-style pattern like "*.py", "tests/test_*.py", or "**/*.md".
        root:
            Root directory to search from. Defaults to the current directory ".".

    Returns:
        A sorted list of matching file paths as strings.
    """
    base = Path(root)
    matches = [str(path) for path in base.rglob(pattern)]
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
    p = Path(path)

    if not p.exists():
        return f"No file found at '{path}'."

    if p.is_dir():
        return f"'{path}' is a directory, not a file. Refusing to delete."

    p.unlink()
    return f"Deleted '{path}'."

# registering the functions on file_toolset - exersice 3
file_toolset.add_function(read_file)
file_toolset.add_function(write_file)
file_toolset.add_function(search_files)
file_toolset.add_function(delete_file)

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
    instructions = "You are a Python coding agent. Write clear, correct, and minimal Python code.",
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