"""
Defines the LinkedIn Profile Analyst Agent for the blog creation workflow.
This agent extracts expertise and story potential from professional experience.
"""

import logging
from crewai import Agent
from langchain.llms import OpenAI, HuggingFaceHub # Using generic imports for demonstration
from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_profile_analyst_agent() -> Agent:
    """
    Initializes and returns the LinkedIn Profile Analyst Agent.

    This agent is responsible for analyzing LinkedIn profiles to identify
    compelling narratives and technical expertise suitable for blog content.

    Returns:
        Agent: The configured Profile Analyst Agent.
    """
    try:
        # Initialize LLM client specific to this agent
        gpt4_client = DualModelChatClient(
            reasoning_model="gpt-4",
            concept_model="gpt-3.5-turbo",
            default_model="reasoning",
        )
        profile_analyst_llm = gpt4_client.get_llm()

        agent = Agent(
            role="LinkedIn Profile Analyst",
            goal="Extract expertise and story potential from professional experience",
            backstory=(
                "You are an expert at analyzing professional profiles to find "
                "compelling narratives and technical expertise that can be "
                "transformed into engaging blog content."
            ),
            llm=profile_analyst_llm,
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Profile Analyst Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Profile Analyst Agent: {e}")
        raise
