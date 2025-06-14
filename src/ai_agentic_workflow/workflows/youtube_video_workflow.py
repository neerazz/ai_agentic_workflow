from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Any
import re

from crewai import Agent, Task, Crew, Process

from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.clients.gemini_client import DualModelGeminiClient
from src.ai_agentic_workflow.clients.claude_client import DualModelClaudeClient

logger = logging.getLogger(__name__)

@dataclass
class VideoProject:
    """Central state object passed between tasks."""
    idea: str
    story_draft: str | None = None
    review_notes: str | None = None
    score: int | None = None
    direction: str | None = None
    attempts: int = 0


class YouTubeVideoWorkflow:
    """Workflow for AI powered video generation using CrewAI."""

    def __init__(self):
        # instantiate clients with appropriate models
        self.story_client = DualModelGeminiClient(
            reasoning_model="gemini-2.5-pro",  # high quality for creative tasks
            concept_model="gemini-2.5-pro",
            default_model="gemini-2.5-pro",
        )
        # reviewer uses GPT-4o for strong reasoning but keeps a cheaper model for concepts
        self.review_client = DualModelChatClient(
            reasoning_model="gpt-4o",
            concept_model="gpt-3.5-turbo",
            default_model="reasoning",
        )
        # enhancer opts for a cheaper ChatGPT model
        self.enhance_client = DualModelChatClient(
            reasoning_model="gpt-3.5-turbo",
            concept_model="gpt-3.5-turbo",
            default_model="gpt-3.5-turbo",
        )
        # director uses Claude Opus for high-end creative direction
        self.direction_client = DualModelClaudeClient(
            reasoning_model="claude-3-opus-20240229",
            concept_model="claude-3-sonnet-20240229",
            default_model="reasoning",
        )

        # define agents with instructions focused on inspirational adult content
        self.storyteller = Agent(
            role="Story Writer",
            goal=(
                "Craft 600-800 word inspirational narratives that weave Buddhist "
                "and Zen wisdom into relatable life lessons for adults"
            ),
            backstory=(
                "Seasoned author known for transforming ancient teachings into "
                "modern, motivational stories that spark personal growth"
            ),
            llm=self.story_client.get_llm(),
        )
        self.reviewer = Agent(
            role="Story Reviewer",
            goal=(
                "Critique each story for authenticity, inspirational value and "
                "clarity, returning a numeric score and revision notes"
            ),
            backstory=(
                "Philosophical editor ensuring wisdom tales resonate with a "
                "broad adult audience and remain culturally respectful"
            ),
            llm=self.review_client.get_llm(model_type="reasoning"),
        )
        self.enhancer = Agent(
            role="Story Enhancer",
            goal="Refine stories using reviewer feedback to deepen emotional impact",
            backstory="Creative writer polishing inspirational scripts for maximum engagement",
            llm=self.enhance_client.get_llm(),
        )
        self.director = Agent(
            role="Creative Director",
            goal="Provide cinematic direction for a 4-5 minute inspirational video",
            backstory="Filmmaker blending ancient wisdom with modern storytelling techniques",
            llm=self.direction_client.get_llm(),
        )

    def _story_task(self, idea: str) -> Task:
        return Task(
            description=(
                "Write a 600-800 word inspirational wisdom story for adults based on the idea '{idea}'. "
                "Follow the structure: opening hook, character intro, conflict, wisdom encounter, transformation, resolution, and modern application. "
                "Keep language simple and conversational."
            ),
            expected_output="Complete narrative story",
            agent=self.storyteller,
        )

    def _review_task(self) -> Task:
        return Task(
            description=(
                "Review the story for authenticity, inspirational impact, emotional resonance and pacing. "
                "Provide a numeric score out of 100 with specific suggestions for improvement."
            ),
            expected_output="Review notes and score",
            agent=self.reviewer,
        )

    def _enhance_task(self) -> Task:
        return Task(
            description=(
                "Rewrite the story incorporating the review notes to strengthen the life lesson and emotional impact while keeping the wise, conversational tone."
            ),
            expected_output="Improved story draft",
            agent=self.enhancer,
        )

    def _direction_task(self) -> Task:
        return Task(
            description=(
                "Summarize the finalized story and provide direction notes for a 4-5 minute inspirational video, including suggested visuals, sound design and pacing."
            ),
            expected_output="Director notes",
            agent=self.director,
        )

    QUALITY_THRESHOLD = 90
    MAX_RETRIES = 3

    def _extract_score(self, review_output: str) -> int:
        match = re.search(r"(\d{1,3})", review_output)
        return int(match.group(1)) if match else 0

    def run(self, idea: str) -> VideoProject:
        project = VideoProject(idea=idea)
        current_story = None
        review_notes = None
        score = 0

        for attempt in range(1, self.MAX_RETRIES + 1):
            project.attempts = attempt
            if current_story is None:
                story_task = self._story_task(idea)
            else:
                story_task = self._enhance_task()

            review_task = self._review_task()
            crew = Crew(
                tasks=[story_task, review_task],
                agents=[story_task.agent, review_task.agent],
                process=Process.sequential,
            )

            inputs = {
                "idea": idea,
                "story": current_story,
                "review_notes": review_notes,
            }

            result = crew.kickoff(inputs)
            task_outputs = result.tasks_output
            current_story = task_outputs[0].raw
            review_notes = task_outputs[1].raw
            score = self._extract_score(review_notes)

            project.story_draft = current_story
            project.review_notes = review_notes
            project.score = score

            if score >= self.QUALITY_THRESHOLD:
                break

        # direction stage
        direction_task = self._direction_task()
        crew = Crew(
            tasks=[direction_task],
            agents=[direction_task.agent],
            process=Process.sequential,
        )
        result = crew.kickoff({"story": current_story})
        project.direction = result.tasks_output[0].raw
        return project


def run_youtube_video_workflow(initial_idea: str) -> Dict[str, Any]:
    """Convenience wrapper to run the workflow and return a dictionary."""
    workflow = YouTubeVideoWorkflow()
    project = workflow.run(initial_idea)
    return {
        "idea": project.idea,
        "story_draft": project.story_draft,
        "review_notes": project.review_notes,
        "direction": project.direction,
    }
