"""
Defines the Blog Quality Reviewer Agent for the blog creation workflow.
This agent ensures blogs are authentic, engaging, and valuable for the target audience.
"""

import logging
from crewai import Agent
from langchain.llms import OpenAI, HuggingFaceHub # Using generic imports for demonstration
from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_blog_critic_agent() -> Agent:
    """
    Initializes and returns the Blog Quality Reviewer Agent.

    This agent is a seasoned editor with a keen eye for authenticity and
    engagement, ensuring technical blogs go viral.

    Returns:
        Agent: The configured Blog Critic Agent.
    """
    try:
        # Initialize LLM client specific to this agent
        gpt4_client = DualModelChatClient(
            reasoning_model="gpt-4",
            concept_model="gpt-3.5-turbo",
            default_model="reasoning",
        )
        blog_critic_llm = gpt4_client.get_llm(model_type="reasoning")

        agent = Agent(
            role="Blog Quality Reviewer",
            goal="Ensure blogs are authentic, engaging, and valuable for the target audience",
            backstory=(
                "You are a seasoned editor who knows what makes technical blogs "
                "go viral. You have a keen eye for authenticity and engagement."
            ),
            llm=blog_critic_llm,
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Blog Critic Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Blog Critic Agent: {e}")
        raise

# Example usage:
if __name__ == "__main__":
    agent = get_blog_critic_agent()
    print(agent)