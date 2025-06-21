"""
Defines the Resource Curator Agent for the blog creation workflow.
This agent connects blog content to broader community resources and discussions.
"""

import json
import logging

from crewai import Agent

from src.ai_agentic_workflow.clients.perplexity_client import DualModelPerplexityClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_community_connector_prompt(blog_content: str, topic: str) -> str:
    """
    Returns the prompt for the Resource Curator Agent.

    Args:
        blog_content (str): The markdown content of the blog post.
        topic (str): JSON string of the blog topic details.

    Returns:
        str: The formatted prompt string.
    """
    return f"""
    Enhance this blog post with community connections and additional resources.

    Blog Post: {blog_content}
    Topic: {topic}
    Target Audience: Junior to mid-level developers

    Your tasks:
    1. Research and add 3-5 highly relevant external resources
    2. Identify thought leaders or experts discussing this topic
    3. Create discussion points for readers to consider
    4. Add beginner-friendly learning resources
    5. Suggest related topics for further exploration

    Integration Requirements:
    - Weave references naturally into the content
    - Add a "Further Learning" section
    - Include "Join the Conversation" prompts
    - Ensure all links are current and accessible
    - Prioritize free resources for job seekers

    OUTPUT FORMAT:
    1. Enhanced blog with integrated references (in markdown)
    2. Separate JSON with:
    {{
        "integrated_references": [
            {{
                "resource": "title",
                "url": "link",
                "integration_point": "where in blog",
                "value_add": "what readers gain"
            }}
        ],
        "further_learning": [
            {{
                "resource": "title",
                "url": "link",
                "difficulty": "beginner/intermediate",
                "time_investment": "X minutes/hours"
            }}
        ],
        "discussion_starters": ["question1", "question2"],
        "community_tags": ["#tag1", "#tag2"],
        "related_topics": ["topic1", "topic2"]
    }}
    """


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


if __name__ == "__main__":
    # Example usage for debugging/testing the agent and its prompt
    from crewai import Task, Crew, Process

    # Initialize the agent
    community_connector = get_community_connector_agent()

    # Example blog content and topic (simplified for example)
    example_blog_content = """
    # My Journey with Serverless Functions

    ...After much trial and error, I finally deployed my first serverless function!
    It was a small Lambda function in AWS, converting image formats. The beauty
    of not managing servers was astounding. I used Python for the function logic.

    In conclusion, serverless is a powerful paradigm...
    """

    example_topic = json.dumps({
        "topic": "Getting Started with AWS Lambda and Python",
        "category": "Cloud/DevOps"
    })

    # Get the prompt for the task
    task_description = get_community_connector_prompt(
        blog_content=example_blog_content,
        topic=example_topic
    )

    # Create a task for the agent
    example_task = Task(
        description=task_description,
        expected_output="Enhanced blog with resources and community connections",
        agent=community_connector
    )

    # Create a dummy crew to run the task
    crew = Crew(
        agents=[community_connector],
        tasks=[example_task],
        process=Process.sequential,
        verbose=True
    )

    print("Running example task for Community Connector Agent...")
    try:
        result = crew.kickoff()
        # The output of this agent includes both markdown and JSON,
        # so we'll just print the raw output as an example.
        print("\n--- Community Connector Agent Example Result ---")
        print(result.tasks_output[0].raw)
    except Exception as e:
        print(f"An error occurred during the example run: {e}")
