from os import getenv
import asyncio
from typing import Any, Callable
from dataclasses import dataclass

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai import Agent, RunContext, ModelSettings

from dotenv import load_dotenv
from rich.console import Console

from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.toolsets import AgentToolset, FunctionToolset
from pydantic_ai.tools import ToolCallPart, ToolDefinition

from skills import Skills
# Load environment variables from .env file
load_dotenv()

#deps type for Exercise 4
@dataclass
class AgentDeps:
    console: Console

# Step 1: Provider & model
provider = OpenAIProvider(
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("API_KEY")
)

model = OpenAIResponsesModel(
    model_name="gpt-5.1-codex-mini",
    provider=provider,
)

# Step 2: file tools & capabilities
# Create a toolset to hold our file tools
file_toolset = FunctionToolset()

def read_file(path: str) -> str:
    """ Read a UTF-8 text file from disk and return its contents as a string.

    Parameters:
        path: Path to the file to read.

    Returns:
        The text contents of the file.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path: str, content: str) -> str:
    """
    Write text content to a UTF-8 file on disk, overwriting if it exists.

    Parameters:
        path: Path to the file to write.
        content: Text content to write.

    Returns:
        A short confirmation message about what was written.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} characters to '{path}'."

# registering the functions on file_toolset
file_toolset.add_function(read_file)
file_toolset.add_function(write_file)

class FileOperations(AbstractCapability[Any]):
    """
    Capability exposing basic file operations (read_file, write_file)
    as tools the agent can call.
    """

    def get_toolset(self) -> AgentToolset[Any] | None:
        return file_toolset

# hook to log tool calls - for Exercise 4
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

# NEW: ReasoningEffort capability (same indent as FileOperations, i.e. top level)
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
            
            return ModelSettings(thinking=effort)

        return _set_reasoning_effort


# Step 3: Agent
agent = Agent(
    model = model,
    instructions = "You are a Python coding agent. Write clear, correct, and minimal Python code.",
    capabilities = [FileOperations(), ReasoningEffort(), Skills()],
    deps_type=AgentDeps,
)

# Steps 4: Conversation loop
async def main() -> None:
    console = Console()
    deps = AgentDeps(console=console)
    
    message_history = None 
    while True: 
        user_input = input("Question: ")
        if user_input.strip().lower() in {"exit", "quit"}:
            break
        
        result = await agent.run(user_input, message_history = message_history, deps = deps,)
        print("\nAssistant:\n")
        print(result.output)
        
        message_history = result.all_messages()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")

