"""
Defines the Tech Trend Researcher Agent for the blog creation workflow.
This agent identifies trending topics relevant to user expertise and audience needs.
"""

import json
import logging

from crewai import Agent

from src.ai_agentic_workflow.clients.perplexity_client import DualModelPerplexityClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_trend_scout_prompt(expertise_areas: str) -> str:
    """
    Returns the prompt for the Tech Trend Researcher Agent.

    Args:
        expertise_areas (str): JSON string of the user's expertise areas.

    Returns:
        str: The formatted prompt string.
    """
    return f"""
    Research current trending topics in software development across multiple platforms.

    Search Scope:
    1. Latest LLM model releases and AI developments
    2. Popular discussions on Dev.to, Medium tech publications, HackerNews
    3. Trending GitHub repositories and technologies
    4. Common developer pain points from Stack Overflow
    5. Most requested skills in job postings
    6. Topics that junior to mid-level developers are struggling with

    Additional Context:
    - User Expertise Areas: {expertise_areas}
    - Target Audience: Junior to mid-level developers, job seekers

    Find 15-20 trending topics that:
    - Are currently generating high engagement
    - Match the user's expertise areas when possible
    - Would be valuable for the target audience
    - Have teaching/learning potential

    OUTPUT FORMAT as JSON:
    {{
        "trending_topics": [
            {{
                "topic": "topic title",
                "category": "AI/Frontend/Backend/DevOps/Career",
                "engagement_score": 0-100,
                "source": "where you found it",
                "relevance_reason": "why this matters now",
                "teaching_potential": "what readers would learn",
                "difficulty_level": "beginner/intermediate"
            }}
        ],
        "emerging_themes": ["theme1", "theme2"],
        "recommended_focus": "suggested priority area based on trends"
    }}

    IMPORTANT: Return ONLY the JSON object, no markdown formatting or additional text.
    """

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
            reasoning_model="sonar-reasoning",
            concept_model="sonar",
            default_model="concept",
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

if __name__ == "__main__":
    # Example usage for debugging/testing the agent and its prompt
    from crewai import Task, Crew, Process

    # Initialize the agent
    trend_scout = get_trend_scout_agent()

    # Example expertise areas (should be a JSON string as expected by the prompt)
    example_expertise = json.dumps({
        "Python": {"years": 5, "proficiency": "expert"},
        "Machine Learning": {"years": 3, "proficiency": "intermediate"}
    })

    # Get the prompt for the task
    task_description = get_trend_scout_prompt(expertise_areas=example_expertise)

    # Create a task for the agent
    example_task = Task(
        description=task_description,
        expected_output="Trending topics with engagement scores in JSON format",
        agent=trend_scout
    )

    # Create a dummy crew to run the task
    crew = Crew(
        agents=[trend_scout],
        tasks=[example_task],
        process=Process.sequential,
        verbose=True
    )

    print("Running example task for Trend Scout Agent...")
    try:
        result = crew.kickoff()
        print("\n--- Trend Scout Agent Example Result ---")
        print(result.tasks_output[0].raw)
    except Exception as e:
        print(f"An error occurred during the example run: {e}")
