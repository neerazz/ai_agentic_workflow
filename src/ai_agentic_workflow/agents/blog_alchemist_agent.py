"""
Defines the Content Enhancement Specialist Agent for the blog creation workflow.
This agent transforms good blogs into exceptional ones based on feedback.
"""

import logging
from crewai import Agent
from langchain.llms import OpenAI, HuggingFaceHub # Using generic imports for demonstration
from src.ai_agentic_workflow.clients.claude_client import DualModelClaudeClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_blog_alchemist_agent() -> Agent:
    """
    Initializes and returns the Content Enhancement Specialist Agent.

    This agent is an expert in content optimization, adding the perfect
    touches to make blogs irresistibly engaging.

    Returns:
        Agent: The configured Blog Alchemist Agent.
    """
    try:
        # Initialize LLM client specific to this agent
        claude_opus_client = DualModelClaudeClient(
            reasoning_model="claude-3-opus-20240229",
            concept_model="claude-3-sonnet-20240229",
            default_model="reasoning",
        )
        blog_alchemist_llm = claude_opus_client.get_llm()

        agent = Agent(
            role="Content Enhancement Specialist",
            goal="Transform good blogs into exceptional ones based on feedback",
            backstory=(
                "You are a content optimization expert who knows how to add "
                "the perfect touches to make blogs irresistibly engaging."
            ),
            llm=blog_alchemist_llm,
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Blog Alchemist Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Blog Alchemist Agent: {e}")
        raise
# Example usage:
if __name__ == "__main__":
    agent = get_blog_alchemist_agent()
    print(agent)