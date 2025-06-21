"""
Defines the Tech Trend Researcher Agent for the blog creation workflow.
This agent identifies trending topics relevant to user expertise and audience needs.
"""

import logging
from crewai import Agent
from langchain.llms import OpenAI, HuggingFaceHub # Using generic imports for demonstration
from src.ai_agentic_workflow.clients.perplexity_client import DualModelPerplexityClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_trend_scout_agent() -> Agent:
    """
    Initializes and returns the Tech Trend Researcher Agent.

    This agent monitors various platforms to discover trending and relevant
    technical topics for developers.

    Returns:
        Agent: The configured Trend Scout Agent.
    """
    try:
        # Initialize LLM client specific to this agent
        perplexity_client = DualModelPerplexityClient(
            reasoning_model="sonar-pro",
            concept_model="sonar",
            default_model="reasoning",
        )
        trend_scout_llm = perplexity_client.get_llm()

        agent = Agent(
            role="Tech Trend Researcher",
            goal="Identify trending topics that match user expertise and audience needs",
            backstory=(
                "You are a tech trend analyst who monitors multiple platforms "
                "to find the most engaging and relevant topics for developers."
            ),
            llm=trend_scout_llm,
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Trend Scout Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Trend Scout Agent: {e}")
        raise

# Example usage:
if __name__ == "__main__":
    agent = get_trend_scout_agent()
    print(agent)