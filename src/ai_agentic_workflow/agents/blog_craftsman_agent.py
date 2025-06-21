"""
Defines the Technical Blog Writer Agent for the blog creation workflow.
This agent writes engaging technical blogs combining storytelling with practical value.
"""

import logging
from crewai import Agent
from langchain.llms import OpenAI, HuggingFaceHub # Using generic imports for demonstration
from src.ai_agentic_workflow.clients.claude_client import DualModelClaudeClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_blog_craftsman_agent() -> Agent:
    """
    Initializes and returns the Technical Blog Writer Agent.

    This agent is known for making complex topics accessible through
    personal stories and clear examples in blog posts.

    Returns:
        Agent: The configured Blog Craftsman Agent.
    """
    try:
        # Initialize LLM client specific to this agent
        claude_opus_client = DualModelClaudeClient(
            reasoning_model="claude-3-opus-20240229",
            concept_model="claude-3-sonnet-20240229",
            default_model="reasoning",
        )
        blog_craftsman_llm = claude_opus_client.get_llm()

        agent = Agent(
            role="Technical Blog Writer",
            goal="Write engaging technical blogs that combine storytelling with practical value",
            backstory=(
                "You are a popular technical blogger known for making complex "
                "topics accessible through personal stories and clear examples."
            ),
            llm=blog_craftsman_llm,
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Blog Craftsman Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Blog Craftsman Agent: {e}")
        raise

# Example usage:
if __name__ == "__main__":
    agent = get_blog_craftsman_agent()
    print(agent)