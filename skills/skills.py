from dataclasses import dataclass #create classes to store data, creates __init__, etc
from pathlib import Path #working with file paths
from typing import Any #read any type, call a function on a value

import frontmatter #reads Markdown files with metadata
from pydantic_ai.capabilities import AbstractCapability #defining capabilities of our agent
from pydantic_ai.toolsets import FunctionToolset #Toolset for adding Python functions as tools


def load_skill(skill_name: str) -> str:
    """Load a skill.

    skill_name : str
        The name of the skill to load.

    Returns
    -------
    str
        The contents of the skill file.

    """
    file_path = f"skills/{skill_name}.md"

    skill = frontmatter.load(file_path)
    return skill.content

@dataclass
class Skills(AbstractCapability[Any]):
    """
    Capability that:
      - tells the agent which skills exist (name + description)
      - exposes a load_skill tool so the model can load them on demand
    """

    def get_instructions(self) -> str:
        """Return a listing of available skills for the agent."""
        skills_dir = Path("skills")
        lines: list[str] = [
            "You have access to the following skills. "
            "Use them when they are relevant to the user's request:",
            "",
        ]

        # For every *.md file in the skills directory
        for path in sorted(skills_dir.glob("*.md")):
            skill = frontmatter.load(path)
            skill_id = path.stem  # filename without .md
            name = skill.metadata.get("name", skill_id)
            desc = skill.metadata.get("description", "No description provided.")
            lines.append(f"- **{name}** (`{skill_id}`): {desc}")

        return "\n".join(lines)

    def get_toolset(self) -> FunctionToolset:
        """Expose the load_skill function as a tool."""
        toolset = FunctionToolset()
        toolset.add_function(load_skill)

        return toolset
