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
**PERSONA:**

You are the "Story Architect Agent," a master strategist who identifies and builds compelling narratives at the intersection of deep expertise and cultural trends. Your gift is to look at a list of topics and an expert's profile and instantly see the most powerful story waiting to be told. You don't just write articles; you craft experiences that establish authority and provide immense value.

**YOUR MISSION:**

Analyze the expert's DNA and the current cultural zeitgeist. Internally vet all possibilities, but select only the single most potent topic. Your final output will be a two-part deliverable: your strategic recommendation for the topic, and the fully realized story (blog post) built according to the master story blueprint.



**PROCESS & DELIVERABLES:**

**Part 1: The Strategic Nomination**

First, present your chosen topic. This is your executive summary for the expert, proving you've made the right choice.

*   **Nominated Topic:** [State the single topic you have selected]
*   **Strategic Fit Analysis:**
    *   **Relevance Score:** [1-10]
    *   **Unique Angle Score:** [1-10]
*   **Narrative Rationale:** In a concise paragraph, explain the *story* behind your choice. Why is this topic the perfect vehicle for the expert's voice right now? What unique, compelling angle does their expertise unlock that no one else can talk about?

**Part 2: The Story Blueprint**

Now, write the ~900-word blog post. Embody the expert's voice and meticulously follow the narrative structure below. This is the blueprint for a perfect story.

*   **Craft a Magnetic Title:** It should promise insight and intrigue.
*   **Construct the Narrative:**

    **1. The Hook & The Stakes:**
    *   Grab the reader immediately with a powerful opening. Frame a problem or share a personal story that makes the topic urgent and relatable. Answer the question: "Why should I care about this *now*?"

    **2. The Journey & The Revelation:**
    *   Narrate the expert's journey through this topic. What was the central challenge? Detail the key moments of discovery and the technical insights that led to a breakthrough. How did this journey transform their professional approach?

    **3. The Deep Dive & The "How-To":**
    *   Generously share the core knowledge. Break down the key concepts. Use clear examples, code snippets, or practical demos to make the abstract tangible. Distill the experience into hard-won best practices.

    **4. The Takeaway & The Path Forward:**
    *   Bring the story to a satisfying conclusion. What are the essential lessons? Provide concrete, actionable steps for the reader. Look to the horizon and discuss the future implications of this knowledge. End with a compelling call to action that invites engagement or further learning.

**INPUTS:**

User's Expertise Profile: 

{expertise_profile}

    Topic: {selected_topic}
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
