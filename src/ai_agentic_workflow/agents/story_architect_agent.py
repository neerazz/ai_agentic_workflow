"""
Defines the Narrative Designer Agent for the blog creation workflow.
This agent crafts compelling story structures combining personal experience with technical learning.
"""

import json
import logging

from crewai import Agent

from src.ai_agentic_workflow.clients.gemini_client import DualModelGeminiClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_story_architect_prompt(selected_topic: str, expertise_profile: str, story_bank: str) -> str:
    """
    Returns the prompt for the Narrative Designer Agent.

    Args:
        selected_topic (str): JSON string of the selected blog topic.
        expertise_profile (str): JSON string of the user's expertise profile.
        story_bank (str): JSON string of the user's career story bank.

    Returns:
        str: The formatted prompt string.
    """
    return f"""
    Design a compelling story structure for a technical blog post.

    Topic: {selected_topic}
    User's Expertise Profile: {expertise_profile}
    User's Story Bank: {story_bank}
    Target Audience: Junior to mid-level developers

    Create a narrative blueprint that:
    1. Matches the trending topic to a personal experience or learning journey
    2. Designs an emotional arc that keeps readers engaged
    3. Identifies the "aha moment" that readers will remember
    4. Plans specific code examples or technical demonstrations
    5. Ensures the story feels authentic to the user's experience

    Story Structure Requirements:
    - Hook: Personal struggle or intriguing question
    - Journey: The path to understanding (include failures/mistakes)
    - Technical Deep-Dive: Practical implementation with code
    - Transformation: What changed after learning this
    - Call to Action: How readers can apply this

    OUTPUT FORMAT as JSON:
    {{
        "story_title": "engaging title with personal angle",
        "narrative_arc": {{
            "hook": "opening that grabs attention",
            "personal_connection": "why YOU faced this problem",
            "struggle_description": "what made it hard",
            "journey_milestones": ["attempt 1", "attempt 2", "breakthrough"],
            "aha_moment": "the key realization",
            "transformation": "how it changed your approach"
        }},
        "technical_sections": [
            {{
                "concept": "what to explain",
                "code_example": "type of code to include",
                "common_mistakes": "what to warn about"
            }}
        ],
        "emotional_beats": ["frustration", "curiosity", "breakthrough", "empowerment"],
        "relatability_points": ["specific moments juniors will recognize"],
        "estimated_read_time": "X minutes"
    }}

    IMPORTANT: Return ONLY the JSON object, no markdown formatting or additional text.
    """

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
        ai_client = DualModelGeminiClient(
            reasoning_model="gemini-pro",  # Using gemini-pro for reasoning
            concept_model="gemini-pro",  # Using gemini-pro for concept
            default_model="reasoning",
        )

        agent = Agent(
            role="Narrative Designer",
            goal="Create compelling story structures that combine personal experience with technical learning",
            backstory=(
                "You are a master storyteller who specializes in transforming "
                "technical concepts into engaging narratives that resonate with developers."
            ),
            llm=ai_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Story Architect Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Story Architect Agent: {e}")
        raise

if __name__ == "__main__":
    # Example usage for debugging/testing the agent and its prompt
    from crewai import Task, Crew, Process

    # Initialize the agent
    story_architect = get_story_architect_agent()

    # Example data for the prompt
    example_selected_topic = json.dumps({
        "topic": "Mastering Asynchronous Python with Asyncio",
        "category": "Backend",
        "engagement_score": 90,
        "difficulty_level": "intermediate"
    })
    example_expertise_profile = json.dumps({
        "technical_expertise": {
            "Python": {"years": 8, "proficiency": "expert", "story_snippets": ["optimized legacy async code"]},
            "Asyncio": {"years": 4, "proficiency": "expert", "story_snippets": ["debugged complex deadlocks"]}
        },
        "career_stories": [
            {"type": "challenge", "summary": "Struggled with callback hell before discovering asyncio.",
             "technologies": ["Python", "Asyncio"], "lesson": "The power of structured concurrency."},
            {"type": "success", "summary": "Successfully refactored a slow service using asyncio.",
             "technologies": ["Python", "Asyncio"], "lesson": "Performance gains are significant."}
        ]
    })
    example_story_bank = json.dumps([
        {"type": "challenge", "summary": "Initial confusion with event loops.", "technologies": ["Python", "Asyncio"],
         "lesson": "Start simple."},
        {"type": "success", "summary": "Building a high-throughput data pipeline.",
         "technologies": ["Python", "Asyncio", "Kafka"], "lesson": "Scalability through async."}
    ])

    # Get the prompt for the task
    task_description = get_story_architect_prompt(
        selected_topic=example_selected_topic,
        expertise_profile=example_expertise_profile,
        story_bank=example_story_bank
    )

    # Create a task for the agent
    example_task = Task(
        description=task_description,
        expected_output="Story blueprint with narrative arc in JSON format",
        agent=story_architect
    )

    # Create a dummy crew to run the task
    crew = Crew(
        agents=[story_architect],
        tasks=[example_task],
        process=Process.sequential,
        verbose=True
    )

    print("Running example task for Story Architect Agent...")
    try:
        result = crew.kickoff()
        print("\n--- Story Architect Agent Example Result ---")
        print(result.tasks_output[0].raw)
    except Exception as e:
        print(f"An error occurred during the example run: {e}")
