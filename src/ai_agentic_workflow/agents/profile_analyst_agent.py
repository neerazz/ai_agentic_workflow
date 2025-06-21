"""
Defines the LinkedIn Profile Analyst Agent for the blog creation workflow.
This agent extracts expertise and story potential from professional experience.
"""
import logging

from crewai import Agent
from crewai import Task, Crew, Process

from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_profile_analyst_prompt(profile_data: str) -> str:
    """
    Returns the prompt for the LinkedIn Profile Analyst Agent.

    Args:
        profile_data (str): The LinkedIn profile data to analyze.

    Returns:
        str: The formatted prompt string.
    """
    return f"""
    Analyze the following LinkedIn profile data to extract expertise and potential story narratives:

    Profile Data:
    {profile_data}

    Your task:
    1. Identify all technical skills and years of experience with each
    2. Extract potential "story moments" from job transitions and projects
    3. Find struggle-to-success narratives that could be used in blog posts
    4. Map technologies to real scenarios from their career
    5. Identify career progression patterns and learning moments

    Focus on finding human stories behind the technical experience that would resonate with junior to mid-level developers.

    OUTPUT FORMAT as JSON:
    {{
        "technical_expertise": {{
            "technology_name": {{
                "years": X,
                "proficiency": "expert/intermediate/learning",
                "story_snippets": ["specific project or challenge", "another story"]
            }}
        }},
        "career_stories": [
            {{
                "type": "challenge/learning/mentoring/success",
                "summary": "brief story description",
                "technologies": ["tech1", "tech2"],
                "lesson": "what readers can learn"
            }}
        ],
        "writing_angles": ["angle1", "angle2"],
        "target_audience_alignment": "how experience matches junior/mid dev needs"
    }}

    IMPORTANT: Return ONLY the JSON object, no markdown formatting or additional text.
    """

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


if __name__ == "__main__":

    # Initialize the agent
    profile_analyst = get_profile_analyst_agent()

    # Example profile data
    example_profile_data = """
    John Doe is a Senior Software Engineer with 8 years of experience in developing
    scalable web applications using Python, Django, and AWS. He led a team of 5
    engineers to migrate a monolithic application to microservices, resulting in
    a 30% reduction in operational costs. He also enjoys mentoring junior developers.
    """

    # Get the prompt for the task
    task_description = get_profile_analyst_prompt(profile_data=example_profile_data)

    # Create a task for the agent
    example_task = Task(
        description=task_description,
        expected_output="Expertise profile and story bank in JSON format",
        agent=profile_analyst
    )

    # Create a dummy crew to run the task
    crew = Crew(
        agents=[profile_analyst],
        tasks=[example_task],
        process=Process.sequential,
        verbose=True
    )

    print("Running example task for Profile Analyst Agent...")
    try:
        result = crew.kickoff()
        print("\n--- Profile Analyst Agent Example Result ---")
        print(result.tasks_output[0].raw)
    except Exception as e:
        print(f"An error occurred during the example run: {e}")
