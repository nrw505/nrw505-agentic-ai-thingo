import os
import logging
from pathlib import Path
from strands import Agent
from strands_tools import calculator
from strands.models import BedrockModel

import retrieve_product_info
import retrieve_pet_care
from inventory_management import get_inventory
from user_management import get_user_by_id, get_user_by_email

logger = logging.getLogger(__name__)

# Configure logging at INFO for all modules
logging.getLogger().setLevel(logging.INFO)

system_prompt = Path("system_prompt.txt").read_text()


def create_agent():
    product_info_kb_id = os.environ.get("KNOWLEDGE_BASE_1_ID")
    pet_care_kb_id = os.environ.get("KNOWLEDGE_BASE_2_ID")
    inventory_management_function = os.environ.get("SYSTEM_FUNCTION_1_NAME")
    user_management_function = os.environ.get("SYSTEM_FUNCTION_2_NAME")

    if not product_info_kb_id or not pet_care_kb_id:
        raise ValueError(
            "Required environment variables KNOWLEDGE_BASE_1_ID and KNOWLEDGE_BASE_2_ID must be set"
        )

    if not inventory_management_function or not user_management_function:
        raise ValueError(
            "Required environment variables SYSTEM_FUNCTION_1_NAME and SYSTEM_FUNCTION_2_NAME must be set"
        )

    model = BedrockModel(
        # model_id="us.amazon.nova-pro-v1:0",
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        # model_id="us.anthropic.claude-opus-4-1-20250805-v1:0",
        max_tokens=4096,
        streaming=False,
        guardrail_id="d17tbnr56lzk",
        guardrail_version="1",
    )

    return Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            retrieve_product_info,
            retrieve_pet_care,
            get_inventory,
            get_user_by_id,
            get_user_by_email,
            # calculator,
        ],
    )


def process_request(prompt):
    """Process a request using the Strands agent"""
    try:
        agent = create_agent()
        response = agent(prompt)
        return str(response)
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing request: {error_message}")

        return {
            "status": "Error",
            "message": "We are sorry for the technical difficulties we are currently facing. We will get back to you with an update once the issue is resolved.",
        }
