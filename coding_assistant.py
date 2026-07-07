from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import ( OpenAIResponsesModel )
from os import getenv
from pydantic_ai import Agent
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuring provider
provider = OpenAIProvider(
    base_url="https://openrouter.ai/api/v1",
    api_key=getenv("API_KEY")
)
print(f"API Key: {getenv('API_KEY')}")
# Configuring model
model = OpenAIResponsesModel(
    model_name="gpt-5.1-codex-mini",
    provider=provider,
)

# Creating an agent
agent = Agent(
    model=model,
    instructions="You are a Python coding agent. Write clear, correct, and minimal Python code.",
)

# Running agent
async def main() -> None:
    try:  # Indented properly
        user_input = input("User input: ")
        result = await agent.run(user_input)
        print("\nAssistant:\n")
        print(result.output)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())