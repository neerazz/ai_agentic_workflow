"""
Defines the Writing Style Analyst Agent for the blog creation workflow.
This agent decodes and codifies unique writing voices from provided text.
"""

import logging
from crewai import Agent
from langchain.llms import OpenAI, HuggingFaceHub # Using generic imports for demonstration
from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_style_decoder_agent() -> Agent:
    """
    Initializes and returns the Writing Style Analyst Agent.

    This agent analyzes writing patterns to create detailed style guides for
    authentic voice replication.

    Returns:
        Agent: The configured Style Decoder Agent.
    """
    try:
        # Initialize LLM client specific to this agent
        gpt4_client = DualModelChatClient(
            reasoning_model="gpt-4",
            concept_model="gpt-3.5-turbo",
            default_model="reasoning",
        )
        style_decoder_llm = gpt4_client.get_llm()

        agent = Agent(
            role="Writing Style Analyst",
            goal="Decode and codify unique writing voice from LinkedIn posts",
            backstory=(
                "You are a linguistic expert who can analyze writing patterns "
                "and create detailed style guides for authentic voice replication."
            ),
            llm=style_decoder_llm,
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Style Decoder Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Style Decoder Agent: {e}")
        raise

# Example usage:
if __name__ == "__main__":
    agent = get_style_decoder_agent()
    print(agent)