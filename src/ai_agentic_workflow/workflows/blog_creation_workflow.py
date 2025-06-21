"""
AI-powered blog creation workflow using CrewAI.
Generates authentic, engaging technical blogs based on personal experience and trending topics.
"""

from __future__ import annotations

import logging
import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from crewai import Agent, Task, Crew, Process
from langchain.tools import Tool

from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.clients.gemini_client import DualModelGeminiClient
from src.ai_agentic_workflow.clients.claude_client import DualModelClaudeClient
from src.ai_agentic_workflow.clients.perplexity_client import DualModelPerplexityClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging
from src.ai_agentic_workflow.utils.prompt_helper import get_prompt_content

setup_logging(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class BlogProject:
    """Central state object for blog creation workflow."""

    linkedin_profile: str
    expertise_profile: Optional[Dict[str, Any]] = None
    trending_topics: Optional[List[Dict[str, Any]]] = None
    selected_topic: Optional[Dict[str, Any]] = None
    story_blueprint: Optional[Dict[str, Any]] = None
    style_guide: Optional[Dict[str, Any]] = None
    linkedin_posts: Optional[List[str]] = None
    blog_draft: Optional[str] = None
    review_feedback: Optional[Dict[str, Any]] = None
    enhanced_blog: Optional[str] = None
    final_blog: Optional[str] = None
    community_resources: Optional[Dict[str, Any]] = None
    attempts: int = 0
    final_score: int = 0


class BlogCreationWorkflow:
    """Workflow for creating authentic, engaging technical blogs."""

    REVIEW_THRESHOLD = 85
    MAX_RETRIES = 3

    def __init__(self) -> None:
        """Initialize the workflow with all necessary clients and agents."""

        # Initialize LLM clients based on agent requirements
        self.gpt4_client = DualModelChatClient(
            reasoning_model="gpt-4",
            concept_model="gpt-3.5-turbo",
            default_model="reasoning",
        )

        self.claude_opus_client = DualModelClaudeClient(
            reasoning_model="claude-3-opus-20240229",
            concept_model="claude-3-sonnet-20240229",
            default_model="reasoning",
        )

        self.gemini_client = DualModelGeminiClient(
            reasoning_model="gemini-pro",
            concept_model="gemini-pro",
            default_model="reasoning",
        )

        self.perplexity_client = DualModelPerplexityClient(
            reasoning_model="sonar-pro",
            concept_model="sonar",
            default_model="reasoning",
        )

        # Create agents
        self._create_agents()

    def _create_agents(self) -> None:
        """Create all agents with their specific roles and capabilities."""

        self.profile_analyst = Agent(
            role="LinkedIn Profile Analyst",
            goal="Extract expertise and story potential from professional experience",
            backstory=(
                "You are an expert at analyzing professional profiles to find "
                "compelling narratives and technical expertise that can be "
                "transformed into engaging blog content."
            ),
            llm=self.gpt4_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        self.trend_scout = Agent(
            role="Tech Trend Researcher",
            goal="Identify trending topics that match user expertise and audience needs",
            backstory=(
                "You are a tech trend analyst who monitors multiple platforms "
                "to find the most engaging and relevant topics for developers."
            ),
            llm=self.perplexity_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        self.story_architect = Agent(
            role="Narrative Designer",
            goal="Create compelling story structures that combine personal experience with technical learning",
            backstory=(
                "You are a master storyteller who specializes in transforming "
                "technical concepts into engaging narratives that resonate with developers."
            ),
            llm=self.claude_opus_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        self.style_decoder = Agent(
            role="Writing Style Analyst",
            goal="Decode and codify unique writing voice from LinkedIn posts",
            backstory=(
                "You are a linguistic expert who can analyze writing patterns "
                "and create detailed style guides for authentic voice replication."
            ),
            llm=self.gpt4_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        self.blog_craftsman = Agent(
            role="Technical Blog Writer",
            goal="Write engaging technical blogs that combine storytelling with practical value",
            backstory=(
                "You are a popular technical blogger known for making complex "
                "topics accessible through personal stories and clear examples."
            ),
            llm=self.claude_opus_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        self.blog_critic = Agent(
            role="Blog Quality Reviewer",
            goal="Ensure blogs are authentic, engaging, and valuable for the target audience",
            backstory=(
                "You are a seasoned editor who knows what makes technical blogs "
                "go viral. You have a keen eye for authenticity and engagement."
            ),
            llm=self.gpt4_client.get_llm(model_type="reasoning"),
            verbose=True,
            allow_delegation=False,
        )

        self.blog_alchemist = Agent(
            role="Content Enhancement Specialist",
            goal="Transform good blogs into exceptional ones based on feedback",
            backstory=(
                "You are a content optimization expert who knows how to add "
                "the perfect touches to make blogs irresistibly engaging."
            ),
            llm=self.claude_opus_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        self.community_connector = Agent(
            role="Resource Curator",
            goal="Connect blog content to broader community resources and discussions",
            backstory=(
                "You are a community builder who knows where developers learn "
                "and discuss topics, always ready with the perfect resources."
            ),
            llm=self.perplexity_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

    def _parse_json_output(self, raw_output: str) -> Dict[str, Any]:
        """Parse JSON from agent output, handling common formatting issues."""
        try:
            cleaned = re.sub(r"```json\s*", "", raw_output)
            cleaned = re.sub(r"```\s*$", "", cleaned)
            json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:  # pragma: no cover - robustness
            logger.error("JSON parsing error: %s", exc)
            logger.debug("Raw output: %s", raw_output)
            return {}

    def _create_tasks(self, project: BlogProject) -> List[Task]:
        """Create all tasks for the blog creation workflow."""
        tasks = []

        profile_task = Task(
            description=f"""
            {get_prompt_content(file_name="blog_profile_analyst_prompt.txt")}
            """.format(profile_data=project.linkedin_profile),
            expected_output="Expertise profile and story bank in JSON format",
            agent=self.profile_analyst,
        )
        tasks.append(profile_task)

        trend_task = Task(
            description=f"""
            {get_prompt_content(file_name="blog_trend_scout_prompt.txt")}
            """.format(
                expertise_areas=json.dumps(
                    project.expertise_profile.get("technical_expertise", {})
                )
                if project.expertise_profile
                else "General software development"
            ),
            expected_output="Trending topics with engagement scores in JSON format",
            agent=self.trend_scout,
            async_execution=True,
        )
        tasks.append(trend_task)

        story_task = Task(
            description=f"""
            {get_prompt_content(file_name="blog_story_architect_prompt.txt")}
            """.format(
                selected_topic=json.dumps(project.selected_topic)
                if project.selected_topic
                else "",
                expertise_profile=json.dumps(project.expertise_profile)
                if project.expertise_profile
                else "",
                story_bank=json.dumps(project.expertise_profile.get("career_stories", []))
                if project.expertise_profile
                else "",
            ),
            expected_output="Story blueprint with narrative arc in JSON format",
            agent=self.story_architect,
            context=[profile_task, trend_task],
        )
        tasks.append(story_task)

        style_task = Task(
            description=f"""
            {get_prompt_content(file_name="blog_style_decoder_prompt.txt")}
            """.format(
                linkedin_posts="\n\n---POST---\n\n".join(project.linkedin_posts)
                if project.linkedin_posts
                else "No posts available"
            ),
            expected_output="Comprehensive style guide in JSON format",
            agent=self.style_decoder,
        )
        tasks.append(style_task)

        craft_task = Task(
            description=f"""
            {get_prompt_content(file_name="blog_craftsman_prompt.txt")}
            """.format(
                story_blueprint=json.dumps(project.story_blueprint)
                if project.story_blueprint
                else "",
                style_guide=json.dumps(project.style_guide)
                if project.style_guide
                else "",
                topic_details=json.dumps(project.selected_topic)
                if project.selected_topic
                else "",
            ),
            expected_output="Complete blog post in markdown format",
            agent=self.blog_craftsman,
            context=[story_task, style_task],
        )
        tasks.append(craft_task)

        review_task = Task(
            description=f"""
            {get_prompt_content(file_name="blog_critic_prompt.txt")}
            """.format(
                blog_content=project.blog_draft if project.blog_draft else "",
                profile_data=project.linkedin_profile,
                style_guide=json.dumps(project.style_guide)
                if project.style_guide
                else "",
            ),
            expected_output="Detailed review with scores and feedback in JSON format",
            agent=self.blog_critic,
            context=[craft_task],
        )
        tasks.append(review_task)

        if project.review_feedback and project.review_feedback.get("overall_score", 0) < self.REVIEW_THRESHOLD:
            enhance_task = Task(
                description=f"""
                {get_prompt_content(file_name="blog_alchemist_prompt.txt")}
                """.format(
                    blog_content=project.blog_draft,
                    review_feedback=json.dumps(project.review_feedback),
                    style_guide=json.dumps(project.style_guide)
                    if project.style_guide
                    else "",
                ),
                expected_output="Enhanced blog post in markdown format",
                agent=self.blog_alchemist,
                context=[review_task],
            )
            tasks.append(enhance_task)

        community_task = Task(
            description=f"""
            {get_prompt_content(file_name="blog_community_connector_prompt.txt")}
            """.format(
                blog_content=project.enhanced_blog or project.blog_draft,
                topic=json.dumps(project.selected_topic)
                if project.selected_topic
                else "",
            ),
            expected_output="Enhanced blog with resources and community connections",
            agent=self.community_connector,
            context=tasks[-1:],
        )
        tasks.append(community_task)

        return tasks

    def select_best_topic(
        self, expertise_profile: Dict[str, Any], trending_topics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Select the best matching topic based on expertise and trends."""
        best_topic = None
        best_score = 0

        user_technologies = set(expertise_profile.get("technical_expertise", {}).keys())

        for topic in trending_topics:
            score = topic.get("engagement_score", 0) * 0.5
            topic_text = f"{topic.get('topic', '')} {topic.get('category', '')}".lower()
            tech_match_score = sum(
                20 for tech in user_technologies if tech.lower() in topic_text
            )
            score += tech_match_score
            if topic.get("difficulty_level") in ["beginner", "intermediate"]:
                score += 10
            if topic.get("teaching_potential"):
                score += 15
            if score > best_score:
                best_score = score
                best_topic = topic

        logger.info("Selected topic '%s' with score %s", best_topic.get("topic"), best_score)
        return best_topic

    def fetch_profile_with_perplexity(self, profile_url: str) -> Tuple[str, List[str]]:
        """Use Perplexity AI to retrieve profile summary and recent posts."""
        try:
            profile_prompt = (
                "Summarize the work experience, roles, responsibilities and skills "
                f"from the LinkedIn profile at {profile_url}."
            )
            posts_prompt = (
                "Provide three representative posts or content snippets from "
                f"the LinkedIn profile at {profile_url}."
            )
            llm = self.perplexity_client.get_llm()
            logger.debug(f"[Perplexity] Requesting profile summary with prompt: {profile_prompt}")
            profile_text = llm.invoke(profile_prompt)  # type: ignore[arg-type]
            logger.debug(f"[Perplexity] Received profile summary: {profile_text}")
            logger.debug(f"[Perplexity] Requesting posts with prompt: {posts_prompt}")
            posts_text = llm.invoke(posts_prompt)  # type: ignore[arg-type]
            logger.debug(f"[Perplexity] Received posts: {posts_text}")
            posts = re.split(r"\n\n+", str(posts_text)) if posts_text else []
            return str(profile_text), posts[:10]
        except Exception as exc:  # pragma: no cover - network issues
            logger.error("Perplexity profile retrieval failed: %s", exc)
            return "", []


    def run(
        self,
        linkedin_profile_data: Optional[str] = None,
        linkedin_profile_url: Optional[str] = None,
        debug: bool = False,
    ) -> BlogProject:
        """Run the complete blog creation workflow."""

        project = BlogProject(linkedin_profile=linkedin_profile_data or linkedin_profile_url)

        if linkedin_profile_url:
            summary, posts = self.fetch_profile_with_perplexity(linkedin_profile_url)
            project.linkedin_posts = posts
            logger.debug(f"LinkedIn profile summary: {summary}")
            logger.debug(f"LinkedIn posts: {posts}")

        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")

        for attempt in range(1, self.MAX_RETRIES + 1):
            project.attempts = attempt
            logger.info("Starting blog creation attempt %s", attempt)
            try:
                tasks = self._create_tasks(project)
                logger.debug(f"Created tasks: {[t.description for t in tasks]}")
                crew = Crew(
                    agents=[
                        self.profile_analyst,
                        self.trend_scout,
                        self.story_architect,
                        self.style_decoder,
                        self.blog_craftsman,
                        self.blog_critic,
                        self.blog_alchemist,
                        self.community_connector,
                    ],
                    tasks=tasks,
                    process=Process.sequential,
                    verbose=debug,
                )

                logger.debug("Kicking off CrewAI workflow...")
                result = crew.kickoff()
                outputs = result.tasks_output
                logger.debug(f"CrewAI outputs: {[o.raw for o in outputs]}")

                project.expertise_profile = self._parse_json_output(outputs[0].raw)
                logger.debug(f"Expertise profile: {project.expertise_profile}")
                project.trending_topics = self._parse_json_output(outputs[1].raw).get("trending_topics", [])
                logger.debug(f"Trending topics: {project.trending_topics}")

                if not project.selected_topic and project.trending_topics:
                    project.selected_topic = self.select_best_topic(
                        project.expertise_profile, project.trending_topics
                    )
                    logger.debug(f"Selected topic: {project.selected_topic}")

                project.story_blueprint = self._parse_json_output(outputs[2].raw)
                logger.debug(f"Story blueprint: {project.story_blueprint}")
                project.style_guide = self._parse_json_output(outputs[3].raw)
                logger.debug(f"Style guide: {project.style_guide}")
                project.blog_draft = outputs[4].raw
                logger.debug(f"Blog draft: {project.blog_draft}")
                project.review_feedback = self._parse_json_output(outputs[5].raw)
                logger.debug(f"Review feedback: {project.review_feedback}")

                current_score = project.review_feedback.get("overall_score", 0)
                project.final_score = current_score

                if current_score < self.REVIEW_THRESHOLD:
                    if len(outputs) > 6:
                        project.enhanced_blog = outputs[6].raw
                        logger.debug(f"Enhanced blog: {project.enhanced_blog}")
                        project.final_blog = outputs[7].raw
                        logger.debug(f"Final blog (after enhancement): {project.final_blog}")
                    else:
                        logger.warning("Enhancement expected but not found in outputs")
                        continue
                else:
                    project.final_blog = outputs[6].raw
                    logger.debug(f"Final blog: {project.final_blog}")

                if len(outputs) > 0:
                    last_output = outputs[-1].raw
                    json_match = re.search(r"\{.*\}", last_output, re.DOTALL)
                    if json_match:
                        try:
                            project.community_resources = json.loads(json_match.group())
                            logger.debug(f"Community resources: {project.community_resources}")
                        except json.JSONDecodeError:  # pragma: no cover - robustness
                            logger.error("Failed to parse community resources JSON")

                if project.final_score >= self.REVIEW_THRESHOLD:
                    logger.info(
                        "Blog created successfully with score %s", project.final_score
                    )
                    break
            except Exception as exc:  # pragma: no cover - network or parsing issues
                logger.error("Error in blog creation attempt %s: %s", attempt, exc)
                if attempt == self.MAX_RETRIES:
                    raise

        return project


def run_blog_creation_workflow(
    linkedin_profile_data: Optional[str] = None,
    linkedin_profile_url: Optional[str] = None,
    debug: bool = False,
) -> Dict[str, Any]:
    """Convenience function to run the blog creation workflow."""
    workflow = BlogCreationWorkflow()
    project = workflow.run(
        linkedin_profile_data=linkedin_profile_data,
        linkedin_profile_url=linkedin_profile_url,
        debug=debug,
    )

    return {
        "expertise_profile": project.expertise_profile,
        "trending_topics": project.trending_topics,
        "selected_topic": project.selected_topic,
        "story_blueprint": project.story_blueprint,
        "style_guide": project.style_guide,
        "blog_draft": project.blog_draft,
        "review_feedback": project.review_feedback,
        "final_blog": project.final_blog,
        "community_resources": project.community_resources,
        "final_score": project.final_score,
        "attempts": project.attempts,
    }


if __name__ == "__main__":  # pragma: no cover - manual test

    result = run_blog_creation_workflow(debug=True, linkedin_profile_url="https://www.linkedin.com/in/neerajkumarsinghb/")

    print("\n=== BLOG CREATION RESULTS ===")
    print(f"Selected Topic: {result['selected_topic'].get('topic', 'N/A')}")
    print(f"Final Score: {result['final_score']}/100")
    print(f"Attempts: {result['attempts']}")
    print("\n=== FINAL BLOG ===")
    print(result["final_blog"])