"""
Defines the Content Enhancement Specialist Agent for the blog creation workflow.
This agent transforms good blogs into exceptional ones based on feedback.
"""

import json
import logging

from crewai import Agent

from src.ai_agentic_workflow.clients.gemini_client import DualModelGeminiClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging

setup_logging(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_blog_alchemist_prompt(blog_content: str, review_feedback: str, style_guide: str) -> str:
    """
    Returns the prompt for the Content Enhancement Specialist Agent.

    Args:
        blog_content (str): The original markdown content of the blog post.
        review_feedback (str): JSON string of the review feedback.
        style_guide (str): JSON string of the writing style guide.

    Returns:
        str: The formatted prompt string.
    """
    return f"""
    Transform this blog post based on the reviewer's feedback to make it more engaging and authentic.

    Original Blog: {blog_content}
    Review Feedback: {review_feedback}
    Style Guide: {style_guide}

    Enhancement Focus:
    1. Address all high-priority improvement areas
    2. Inject more personality and specific details
    3. Strengthen the personal narrative
    4. Improve code examples with common pitfalls
    5. Add more conversational elements
    6. Ensure it's impossible to tell this is AI-assisted

    Specific Techniques:
    - Add dialogue or internal thoughts ("I remember thinking...")
    - Include specific details (days, times, project names)
    - Add more vulnerability ("I was completely stuck...")
    - Enhance transitions between sections
    - Include "plot twists" or unexpected turns
    - Add humor where appropriate
    - Make technical explanations more accessible

    Maintain:
    - The original story structure
    - Core technical content
    - Overall message and lessons
    - Target word count (600-800 words)

    OUTPUT: Enhanced blog post in markdown format that addresses all feedback while maintaining authenticity.
    """

def get_blog_alchemist_agent() -> Agent:
    """
    Initializes and returns the Content Enhancement Specialist Agent.

    This agent is an expert in content optimization, adding the perfect
    touches to make blogs irresistibly engaging.

    Returns:
        Agent: The configured Blog Alchemist Agent.
    """
    try:

        ai_client = DualModelGeminiClient(
            reasoning_model="gemini-pro",  # Using gemini-pro for reasoning
            concept_model="gemini-pro",  # Using gemini-pro for concept
            default_model="reasoning",
        )

        agent = Agent(
            role="Content Enhancement Specialist",
            goal="Transform good blogs into exceptional ones based on feedback",
            backstory=(
                "You are a content optimization expert who knows how to add "
                "the perfect touches to make blogs irresistibly engaging."
            ),
            llm=ai_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )
        logger.debug("Blog Alchemist Agent initialized successfully.")
        return agent
    except Exception as e:
        logger.error(f"Error initializing Blog Alchemist Agent: {e}")
        raise

if __name__ == "__main__":
    # Example usage for debugging/testing the agent and its prompt
    from crewai import Task, Crew, Process

    # Initialize the agent
    blog_alchemist = get_blog_alchemist_agent()

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

    example_review_feedback = json.dumps({
        "overall_score": 70,
        "category_scores": {
            "storytelling": {"score": 20, "feedback": "Needs more personal anecdotes and emotional depth."},
            "technical_value": {"score": 20, "feedback": "Code examples are too basic, lack real-world context."},
            "authenticity": {"score": 15, "feedback": "Sounds a bit generic, less like a personal story."},
            "engagement": {"score": 15, "feedback": "Hook is weak, lacks strong call to action."}
        },
        "strengths": ["Clear structure", "Accurate technical information"],
        "improvement_areas": [
            {"issue": "Lack of personal struggle details",
             "suggestion": "Expand on the specific challenges faced and how they felt.", "priority": "high"},
            {"issue": "Code examples too simple",
             "suggestion": "Provide a more complex, realistic example that highlights common pitfalls.",
             "priority": "high"},
            {"issue": "Generic opening",
             "suggestion": "Start with a more compelling, specific personal story or a shocking revelation.",
             "priority": "medium"}
        ],
        "ai_detection_risk": "medium",
        "recommendation": "revise"
    })

    example_style_guide = json.dumps({
        "voice_profile": {"tone": "conversational and encouraging", "formality_level": "casual",
                          "humor_style": "self-deprecating"},
        "authenticity_markers": {"learning_admissions": "openly discusses mistakes",
                                 "vulnerability_phrases": ["'I was completely stumped'"]},
        "code_explanation_style": "line-by-line, explaining 'why'"
    })

    # Get the prompt for the task
    task_description = get_blog_alchemist_prompt(
        blog_content=example_blog_content,
        review_feedback=example_review_feedback,
        style_guide=example_style_guide
    )

    # Create a task for the agent
    example_task = Task(
        description=task_description,
        expected_output="Enhanced blog post in markdown format",
        agent=blog_alchemist
    )

    # Create a dummy crew to run the task
    crew = Crew(
        agents=[blog_alchemist],
        tasks=[example_task],
        process=Process.sequential,
        verbose=True
    )

    print("Running example task for Blog Alchemist Agent...")
    try:
        result = crew.kickoff()
        print("\n--- Blog Alchemist Agent Example Result ---")
        print(result.tasks_output[0].raw)
    except Exception as e:
        print(f"An error occurred during the example run: {e}")
