"""
Defines the Technical Blog Writer Agent for the blog creation workflow.
This agent writes engaging technical blogs combining storytelling with practical value.
"""

import json
import logging

from crewai import Agent

from src.ai_agentic_workflow.clients.gemini_client import DualModelGeminiClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_blog_craftsman_prompt(story_blueprint: str, style_guide: str, topic_details: str) -> str:
    """
    Returns the prompt for the Technical Blog Writer Agent.

    Args:
        story_blueprint (str): JSON string of the story blueprint.
        style_guide (str): JSON string of the writing style guide.
        topic_details (str): JSON string of the topic details.

    Returns:
        str: The formatted prompt string.
    """
    return f"""
    Write a complete technical blog post using the provided story blueprint and style guide.

    Story Blueprint: {story_blueprint}
    Style Guide: {style_guide}
    Topic Details: {topic_details}
    Target Length: 600-800 words (2-3 minute read)

    Writing Requirements:
    1. Start with a personal hook that immediately connects with readers
    2. Use the exact voice and style patterns from the style guide
    3. Follow the narrative arc from the blueprint
    4. Include practical code examples with explanations
    5. Share genuine struggles and "failed attempts" before success
    6. Add conversational transitions and personality
    7. End with encouragement and clear next steps

    Structure:
    - Hook (10%): Personal struggle or relatable question
    - Context (15%): Why this matters right now
    - Journey (30%): Your experience, including mistakes
    - Technical Deep-Dive (30%): Code examples with explanations
    - Lessons & Takeaways (10%): What you learned
    - Call to Action (5%): Encourage readers to try

    Remember:
    - Write like you're explaining to a friend who needs help
    - Include specific details ("On that Tuesday morning...")
    - Use humor and vulnerability appropriately
    - Make technical concepts accessible
    - Focus on helping junior/mid-level developers

    OUTPUT: Complete blog post in markdown format with proper headings, code blocks, and formatting.
    """

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
        ai_client = DualModelGeminiClient(
            reasoning_model="gemini-pro",  # Using gemini-pro for reasoning
            concept_model="gemini-pro",  # Using gemini-pro for concept
            default_model="reasoning",
        )

        agent = Agent(
            role="Technical Blog Writer",
            goal="Write engaging technical blogs that combine storytelling with practical value",
            backstory=(
                "You are a popular technical blogger known for making complex "
                "topics accessible through personal stories and clear examples."
            ),
            llm=ai_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Blog Craftsman Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Blog Craftsman Agent: {e}")
        raise

if __name__ == "__main__":
    # Example usage for debugging/testing the agent and its prompt
    from crewai import Task, Crew, Process

    # Initialize the agent
    blog_craftsman = get_blog_craftsman_agent()

    # Example data for the prompt (simplified for example)
    example_story_blueprint = json.dumps({
        "story_title": "My First Encounter with Microservices: A Journey from Monolith to Modularity",
        "narrative_arc": {
            "hook": "Remember the dread of deploying a single, giant codebase?",
            "personal_connection": "I faced this nightmare with our e-commerce platform.",
            "struggle_description": "Every small change meant a risky, hours-long deployment.",
            "journey_milestones": ["Researching alternatives", "Pilot project", "Full migration"],
            "aha_moment": "Seeing independent services deploy in minutes.",
            "transformation": "Agile, scalable, and happier teams."
        },
        "technical_sections": [
            {"concept": "What are microservices?", "code_example": "Diagram of microservice architecture",
             "common_mistakes": "Over-splitting services."},
            {"concept": "Implementing with Python/FastAPI", "code_example": "Simple FastAPI service code",
             "common_mistakes": "Ignoring data consistency."},
        ],
        "emotional_beats": ["frustration", "excitement", "relief"],
        "relatability_points": ["monolith pain", "deployment anxiety"],
        "estimated_read_time": "7 minutes"
    })
    example_style_guide = json.dumps({
        "voice_profile": {"tone": "conversational and encouraging", "formality_level": "casual",
                          "humor_style": "self-deprecating", "personality_markers": ["relatable", "problem-solver"]},
        "structural_patterns": {"opening_styles": ["question", "anecdote"],
                                "transition_phrases": ["'So, what did I do?'", "'Here's the twist:'"],
                                "closing_patterns": ["summary with next steps", "invitation for discussion"]},
        "engagement_techniques": {"question_types": ["rhetorical"], "cta_style": "gentle suggestions",
                                  "hook_patterns": ["problem-solution"]},
        "authenticity_markers": {"vulnerability_phrases": ["'I totally messed up here'", "'It wasn't easy'"],
                                 "learning_admissions": "openly discusses mistakes",
                                 "encouragement_style": "empowering readers to try"},
        "unique_expressions": ["'aha moment'", "'developer's nightmare'"],
        "code_explanation_style": "line-by-line, explaining 'why' not just 'what'",
        "storytelling_rhythm": "fast-paced introduction, detailed middle, reflective ending"
    })
    example_topic_details = json.dumps({
        "topic": "Migrating to Microservices: My Journey to Scalability",
        "category": "DevOps",
        "engagement_score": 85,
        "difficulty_level": "intermediate"
    })

    # Get the prompt for the task
    task_description = get_blog_craftsman_prompt(
        story_blueprint=example_story_blueprint,
        style_guide=example_style_guide,
        topic_details=example_topic_details
    )

    # Create a task for the agent
    example_task = Task(
        description=task_description,
        expected_output="Complete blog post in markdown format",
        agent=blog_craftsman
    )

    # Create a dummy crew to run the task
    crew = Crew(
        agents=[blog_craftsman],
        tasks=[example_task],
        process=Process.sequential,
        verbose=True
    )

    print("Running example task for Blog Craftsman Agent...")
    try:
        result = crew.kickoff()
        print("\n--- Blog Craftsman Agent Example Result ---")
        print(result.tasks_output[0].raw)
    except Exception as e:
        print(f"An error occurred during the example run: {e}")
