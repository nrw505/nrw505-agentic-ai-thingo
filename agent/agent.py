import logging

from strands import Agent, tool
from strands.models import BedrockModel
from strands_tools import calculator, current_time


@tool
def letter_counter(word: str, letter: str) -> int:
    """Count occurrences of a letter in a word."""
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0

    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")

    return word.lower().count(letter.lower())


# Enables Strands debug log level
logging.getLogger("strands").setLevel(logging.DEBUG)

# Sets the logging format and streams logs to stderr
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s", handlers=[logging.StreamHandler()]
)

# Initialize the Bedrock model with a specific model ID and region
model = BedrockModel(model_id="us.anthropic.claude-sonnet-4-20250514-v1:0")


# Create an agent with tools from the community-driven strands-tools package
# as well as our custom letter_counter tool
agent = Agent(model=model, tools=[calculator, current_time, letter_counter])
