## Coding Assistant

This project is a small, sandboxed coding assistant that runs in your terminal.  
It uses Pydantic AI and OpenAI-compatible models to turn natural language
instructions into real actions on your project files.

The repo contains two small, terminal-based coding assistants:

1. The **coding_assistant**
A minimal version implemented step‑by‑step following the masterclass
instructions. It can:

- Maintain **conversation history** across turns, so it remembers what you asked before.
- Use custom **file tools** to:
  - read and open files (e.g. in VS Code),
  - search for files by glob patterns,
  - create folders,
  - move files between folders,
  - and delete files with confirmation.
- Stay safely **restricted to the project root** (no access outside the `coding_assistant` directory).
- Adjust its **reasoning effort** (low / medium / high) based on your request.
- Load extra behavior dynamically through **Markdown-based “skills”**.

2. **improved_assistant**  
An assistant with extended features:
- **Sandboxed file access**: the agent is restricted to the project root
(no access outside the `coding_assistant` directory).
- **Safer deletion**: before deleting a file, it always asks for
user confirmation in the terminal.
- **New capabilities**:
     - create folders inside the project,
     - move files between folders using relative paths.
