"""
Defines the Blog Quality Reviewer Agent for the blog creation workflow.
This agent ensures blogs are authentic, engaging, and valuable for the target audience.
"""

import json
import logging

from crewai import Agent

from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_blog_critic_prompt(blog_content: str, profile_data: str, style_guide: str) -> str:
    """
    Returns the prompt for the Blog Quality Reviewer Agent.

    Args:
        blog_content (str): The markdown content of the blog post.
        profile_data (str): The author's LinkedIn profile data.
        style_guide (str): JSON string of the writing style guide.

    Returns:
        str: The formatted prompt string.
    """
    return f"""
    Review this technical blog post with the critical eye of a popular tech blogger.

    Blog Post: {blog_content}
    Author's LinkedIn Profile: {profile_data}
    Style Guide: {style_guide}
    Target Audience: Junior to mid-level developers

    Evaluate the blog using these criteria:

    **Storytelling Quality (30 points)**
    - Personal anecdote presence and authenticity
    - Emotional journey clarity
    - Relatability for target audience
    - Narrative flow and pacing

    **Technical Value (25 points)**
    - Code example quality and clarity
    - Practical applicability
    - Learning progression (easy to hard)
    - Accuracy of technical information

    **Authenticity Check (25 points)**
    - Matches LinkedIn experience believably
    - Consistent with documented writing style
    - Natural voice (not AI-sounding)
    - Vulnerable/honest moments present

    **Engagement Factors (20 points)**
    - Hook strength (would you keep reading?)
    - Readability and flow
    - Actionable takeaways
    - Comment-worthy content
    - Share-ability factor

    Red Flags to Identify:
    - Generic AI phrases ("In today's fast-paced world...")
    - Missing personal touches
    - Code without context or explanation
    - No clear story arc
    - Inconsistencies with profile experience

    OUTPUT FORMAT as JSON:
    {{
        "overall_score": 0-100,
        "category_scores": {{
            "storytelling": {{"score": 0-30, "feedback": "specific observations"}},
            "technical_value": {{"score": 0-25, "feedback": "specific observations"}},
            "authenticity": {{"score": 0-25, "feedback": "specific observations"}},
            "engagement": {{"score": 0-20, "feedback": "specific observations"}}
        }},
        "strengths": ["strength1", "strength2"],
        "improvement_areas": [
            {{
                "issue": "specific problem",
                "suggestion": "how to fix it",
                "priority": "high/medium/low"
            }}
        ],
        "ai_detection_risk": "low/medium/high",
        "recommendation": "publish/revise/rewrite"
    }}

    IMPORTANT: Return ONLY the JSON object, no markdown formatting or additional text.
    """

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

if __name__ == "__main__":
    # Example usage for debugging/testing the agent and its prompt
    from crewai import Task, Crew, Process

    # Initialize the agent
    blog_critic = get_blog_critic_agent()

    # Example blog content (simplified for example)
    example_blog_content = """
    # My Journey to Understanding Kubernetes Pods

    Hey everyone! Remember when you first heard about Kubernetes and it sounded like
    a dark art? That was me a year ago. I struggled for weeks to grasp the concept
    of Pods...

    ```python
    # Example Python code for a simple web app
    from flask import Flask
    app = Flask(__name__)
    @app.route('/')
    def hello_world():
        return 'Hello, World!'
    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)
    ```

    ...and then it clicked! The key was realizing Pods are the smallest deployable units.
    """

    example_profile_data = """
    Jane Doe, DevOps Engineer. Expertise in Python, Docker, Kubernetes.
    Experience with deploying scalable applications. Likes sharing practical insights.
    """

    example_style_guide = json.dumps({
        "voice_profile": {"tone": "conversational and encouraging", "formality_level": "casual"},
        "authenticity_markers": {"learning_admissions": "openly discusses mistakes"},
        "code_explanation_style": "briefly introduces, then shows code"
    })

    # Get the prompt for the task
    task_description = get_blog_critic_prompt(
        blog_content=example_blog_content,
        profile_data=example_profile_data,
        style_guide=example_style_guide
    )

    # Create a task for the agent
    example_task = Task(
        description=task_description,
        expected_output="Detailed review with scores and feedback in JSON format",
        agent=blog_critic
    )

    # Create a dummy crew to run the task
    crew = Crew(
        agents=[blog_critic],
        tasks=[example_task],
        process=Process.sequential,
        verbose=True
    )

    print("Running example task for Blog Critic Agent...")
    try:
        result = crew.kickoff()
        print("\n--- Blog Critic Agent Example Result ---")
        print(result.tasks_output[0].raw)
    except Exception as e:
        print(f"An error occurred during the example run: {e}")
