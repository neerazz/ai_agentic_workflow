"""
Defines the Writing Style Analyst Agent for the blog creation workflow.
This agent decodes and codifies unique writing voices from provided text.
"""

import logging

from crewai import Agent

from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_style_decoder_prompt(linkedin_posts: str) -> str:
    """
    Returns the prompt for the Writing Style Analyst Agent.

    Args:
        linkedin_posts (str): A string containing concatenated LinkedIn posts.

    Returns:
        str: The formatted prompt string.
    """
    return f"""
    Analyze the following LinkedIn posts to decode the author's unique writing style:

    LinkedIn Posts:
    {linkedin_posts}

    Extract and codify:
    1. Voice characteristics (formal/casual, humor style, personality traits)
    2. Structural patterns (how they start posts, transition between ideas)
    3. Engagement techniques (questions, calls to action, hooks)
    4. Code explanation approach (if present)
    5. Vulnerability patterns (how they admit mistakes or share learning)
    6. Unique phrases or expressions they frequently use
    7. Storytelling techniques

    Create a comprehensive style guide that another writer could use to mimic this voice authentically.

    OUTPUT FORMAT as JSON:
    {{
        "voice_profile": {{
            "tone": "description of overall tone",
            "formality_level": "casual/professional/mixed",
            "humor_style": "self-deprecating/witty/none",
            "personality_markers": ["trait1", "trait2"]
        }},
        "structural_patterns": {{
            "opening_styles": ["pattern1", "pattern2"],
            "transition_phrases": ["phrase1", "phrase2"],
            "closing_patterns": ["pattern1", "pattern2"]
        }},
        "engagement_techniques": {{
            "question_types": ["rhetorical", "direct"],
            "cta_style": "how they ask for engagement",
            "hook_patterns": ["pattern1", "pattern2"]
        }},
        "authenticity_markers": {{
            "vulnerability_phrases": ["phrase1", "phrase2"],
            "learning_admissions": "how they talk about mistakes",
            "encouragement_style": "how they motivate readers"
        }},
        "unique_expressions": ["signature phrase1", "phrase2"],
        "code_explanation_style": "how they introduce and explain code",
        "storytelling_rhythm": "pacing and flow characteristics"
    }}

    IMPORTANT: Return ONLY the JSON object, no markdown formatting or additional text.
    """

def get_style_decoder_agent() -> Agent:
    """
    Initializes and returns the Writing Style Analyst Agent.

    This agent analyzes writing patterns to create detailed style guides for
    authentic voice replication.

    Returns:
        Agent: The configured Style Decoder Agent.
    """
    try:
        # Initialize LLM client specific to this agent
        gpt4_client = DualModelChatClient(
            reasoning_model="gpt-4",
            concept_model="gpt-3.5-turbo",
            default_model="reasoning",
        )
        style_decoder_llm = gpt4_client.get_llm()

        agent = Agent(
            role="Writing Style Analyst",
            goal="Decode and codify unique writing voice from LinkedIn posts",
            backstory=(
                "You are a linguistic expert who can analyze writing patterns "
                "and create detailed style guides for authentic voice replication."
            ),
            llm=style_decoder_llm,
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Style Decoder Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Style Decoder Agent: {e}")
        raise

if __name__ == "__main__":
    # Example usage for debugging/testing the agent and its prompt
    from crewai import Task, Crew, Process

    # Initialize the agent
    style_decoder = get_style_decoder_agent()

    # Example LinkedIn posts data
    example_linkedin_posts = """
    ---POST---
    Just shipped a new feature! The journey was tough, battling
    with obscure database errors for days. But after countless debugging
    sessions and a few cups of coffee, we finally cracked it.
    Lesson learned: Patience and persistence pay off! #SoftwareDev #Debugging

    ---POST---
    Thinking about the future of AI in coding. Will LLMs replace developers?
    I believe they'll be powerful assistants, enhancing our creativity and speed.
    What are your thoughts? Drop them in the comments! #AI #FutureOfTech

    ---POST---
    Had a hilarious bug today! My loop was running infinitely because I forgot
    a simple break condition. Classic rookie mistake, even after 10 years! 😂
    It reminded me that we're all constantly learning. #CodingHumor #Learning
    """

    # Get the prompt for the task
    task_description = get_style_decoder_prompt(linkedin_posts=example_linkedin_posts)

    # Create a task for the agent
    example_task = Task(
        description=task_description,
        expected_output="Comprehensive style guide in JSON format",
        agent=style_decoder
    )

    # Create a dummy crew to run the task
    crew = Crew(
        agents=[style_decoder],
        tasks=[example_task],
        process=Process.sequential,
        verbose=True
    )

    print("Running example task for Style Decoder Agent...")
    try:
        result = crew.kickoff()
        print("\n--- Style Decoder Agent Example Result ---")
        print(result.tasks_output[0].raw)
    except Exception as e:
        print(f"An error occurred during the example run: {e}")
