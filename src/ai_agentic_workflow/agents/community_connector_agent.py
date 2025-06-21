"""
Defines the Resource Curator Agent for the blog creation workflow.
This agent connects blog content to broader community resources and discussions.
"""

import logging
from crewai import Agent
from langchain.llms import OpenAI, HuggingFaceHub # Using generic imports for demonstration
from src.ai_agentic_workflow.clients.perplexity_client import DualModelPerplexityClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_community_connector_agent() -> Agent:
    """
    Initializes and returns the Resource Curator Agent.

    This agent is a community builder who knows where developers learn and
    discuss topics, always ready with relevant resources.

    Returns:
        Agent: The configured Community Connector Agent.
    """
    try:
        # Initialize LLM client specific to this agent
        perplexity_client = DualModelPerplexityClient(
            reasoning_model="sonar-pro",
            concept_model="sonar",
            default_model="reasoning",
        )
        community_connector_llm = perplexity_client.get_llm()

        agent = Agent(
            role="Resource Curator",
            goal="Connect blog content to broader community resources and discussions",
            backstory=(
                "You are a community builder who knows where developers learn "
                "and discuss topics, always ready with the perfect resources."
            ),
            llm=community_connector_llm,
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Community Connector Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Community Connector Agent: {e}")
        raise
# Example usage:
if __name__ == "__main__":
    agent = get_community_connector_agent()
    print(agent)