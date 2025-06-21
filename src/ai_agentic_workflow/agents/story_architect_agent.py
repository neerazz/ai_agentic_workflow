"""
Defines the Narrative Designer Agent for the blog creation workflow.
This agent crafts compelling story structures combining personal experience with technical learning.
"""

import logging
from crewai import Agent
from langchain.llms import OpenAI, HuggingFaceHub # Using generic imports for demonstration
from src.ai_agentic_workflow.clients.claude_client import DualModelClaudeClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_story_architect_agent() -> Agent:
    """
    Initializes and returns the Narrative Designer Agent.

    This agent specializes in transforming technical concepts into engaging
    narratives that resonate with developers.

    Returns:
        Agent: The configured Story Architect Agent.
    """
    try:
        # Initialize LLM client specific to this agent
        claude_opus_client = DualModelClaudeClient(
            reasoning_model="claude-3-opus-20240229",
            concept_model="claude-3-sonnet-20240229",
            default_model="reasoning",
        )
        story_architect_llm = claude_opus_client.get_llm()

        agent = Agent(
            role="Narrative Designer",
            goal="Create compelling story structures that combine personal experience with technical learning",
            backstory=(
                "You are a master storyteller who specializes in transforming "
                "technical concepts into engaging narratives that resonate with developers."
            ),
            llm=story_architect_llm,
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Story Architect Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Story Architect Agent: {e}")
        raise

# Example usage:
if __name__ == "__main__":
    agent = get_story_architect_agent()
    print(agent)