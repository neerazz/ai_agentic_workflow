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

from src.ai_agentic_workflow.clients.perplexity_client import DualModelPerplexityClient
from src.ai_agentic_workflow.utils.logging_config import setup_logging
from src.ai_agentic_workflow.utils.prompt_helper import get_prompt_content

# Import the refactored agents
from src.ai_agentic_workflow.agents.profile_analyst_agent import get_profile_analyst_agent
from src.ai_agentic_workflow.agents.trend_scout_agent import get_trend_scout_agent
from src.ai_agentic_workflow.agents.story_architect_agent import get_story_architect_agent
from src.ai_agentic_workflow.agents.style_decoder_agent import get_style_decoder_agent
from src.ai_agentic_workflow.agents.blog_craftsman_agent import get_blog_craftsman_agent
from src.ai_agentic_workflow.agents.blog_critic_agent import get_blog_critic_agent
from src.ai_agentic_workflow.agents.blog_alchemist_agent import get_blog_alchemist_agent
from src.ai_agentic_workflow.agents.community_connector_agent import get_community_connector_agent


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
        # Initialize LLM client used specifically by the workflow (e.g., for Perplexity profile fetch)
        self.perplexity_client = DualModelPerplexityClient(
            reasoning_model="sonar-pro",
            concept_model="sonar",
            default_model="reasoning",
        )
        # Create agents by calling their respective functions
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """Initialize all agents by calling their dedicated creation functions."""
        try:
            self.profile_analyst = get_profile_analyst_agent()
            self.trend_scout = get_trend_scout_agent()
            self.story_architect = get_story_architect_agent()
            self.style_decoder = get_style_decoder_agent()
            self.blog_craftsman = get_blog_craftsman_agent()
            self.blog_critic = get_blog_critic_agent()
            self.blog_alchemist = get_blog_alchemist_agent()
            self.community_connector = get_community_connector_agent()
            logger.info("All agents initialized successfully within the workflow.")
        except Exception as e:
            logger.critical(f"Failed to initialize one or more agents: {e}")
            raise


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
            # Attempt to find the first '{' and last '}' to salvage JSON
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1 and start < end:
                try:
                    return json.loads(cleaned[start:end+1])
                except json.JSONDecodeError:
                    pass # Failed again, return empty dict

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

        # Conditional enhancement task
        if project.review_feedback and project.review_feedback.get("overall_score", 0) < self.REVIEW_THRESHOLD:
            logger.info("Review score below threshold, adding enhancement task.")
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
        else:
            logger.info("Review score met threshold, skipping enhancement task.")


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
            context=tasks[-1:], # Context should be the last task added, either craft or enhance
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
        return best_topic if best_topic else {} # Ensure a dict is always returned

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
                # Ensure all agents are available before creating the crew
                all_agents = [
                    self.profile_analyst,
                    self.trend_scout,
                    self.story_architect,
                    self.style_decoder,
                    self.blog_craftsman,
                    self.blog_critic,
                    self.blog_alchemist,
                    self.community_connector,
                ]
                # Filter out None agents if any initialization failed (though it should raise an exception)
                available_agents = [agent for agent in all_agents if agent is not None]

                if not available_agents:
                    logger.error("No agents available to run the crew. Exiting.")
                    raise ValueError("No agents initialized for the workflow.")


                logger.debug(f"Created tasks: {[t.description for t in tasks]}")
                crew = Crew(
                    agents=available_agents,
                    tasks=tasks,
                    process=Process.sequential,
                    verbose=debug,
                )

                logger.debug("Kicking off CrewAI workflow...")
                result = crew.kickoff()
                outputs = result.tasks_output
                logger.debug(f"CrewAI raw outputs: {[o.raw for o in outputs]}")

                # Process outputs
                if len(outputs) > 0:
                    project.expertise_profile = self._parse_json_output(outputs[0].raw)
                    logger.debug(f"Expertise profile: {project.expertise_profile}")
                if len(outputs) > 1:
                    project.trending_topics = self._parse_json_output(outputs[1].raw).get("trending_topics", [])
                    logger.debug(f"Trending topics: {project.trending_topics}")

                if not project.selected_topic and project.trending_topics:
                    project.selected_topic = self.select_best_topic(
                        project.expertise_profile, project.trending_topics
                    )
                    logger.debug(f"Selected topic: {project.selected_topic}")

                if len(outputs) > 2:
                    project.story_blueprint = self._parse_json_output(outputs[2].raw)
                    logger.debug(f"Story blueprint: {project.story_blueprint}")
                if len(outputs) > 3:
                    project.style_guide = self._parse_json_output(outputs[3].raw)
                    logger.debug(f"Style guide: {project.style_guide}")
                if len(outputs) > 4:
                    project.blog_draft = outputs[4].raw
                    logger.debug(f"Blog draft: {project.blog_draft}")
                if len(outputs) > 5:
                    project.review_feedback = self._parse_json_output(outputs[5].raw)
                    logger.debug(f"Review feedback: {project.review_feedback}")

                current_score = project.review_feedback.get("overall_score", 0) if project.review_feedback else 0
                project.final_score = current_score

                # Determine which output contains the final blog based on review score
                if current_score < self.REVIEW_THRESHOLD:
                    if len(outputs) > 6:
                        project.enhanced_blog = outputs[6].raw
                        logger.debug(f"Enhanced blog: {project.enhanced_blog}")
                        if len(outputs) > 7: # If enhancement happened, final blog is typically the next output
                            project.final_blog = outputs[7].raw
                            project.community_resources = self._parse_json_output(outputs[8].raw) if len(outputs) > 8 else {}
                        else:
                            logger.warning("Community resources task output not found after enhancement.")
                            project.final_blog = project.enhanced_blog # Fallback if community task output is missing
                    else:
                        logger.warning("Enhancement expected but corresponding output not found.")
                        project.final_blog = project.blog_draft # Fallback to draft if enhancement failed
                else:
                    if len(outputs) > 6: # If no enhancement, the 6th output is community, 7th is final
                        project.final_blog = outputs[6].raw
                        project.community_resources = self._parse_json_output(outputs[7].raw) if len(outputs) > 7 else {}
                    else:
                        logger.warning("Final blog or community resources output missing when review met threshold.")
                        project.final_blog = project.blog_draft


                if project.final_score >= self.REVIEW_THRESHOLD:
                    logger.info(
                        "Blog created successfully with score %s", project.final_score
                    )
                    break
            except Exception as exc: # Catching broad exceptions for retry logic
                logger.error("Error in blog creation attempt %s: %s", attempt, exc, exc_info=True)
                if attempt == self.MAX_RETRIES:
                    logger.critical("Maximum retries reached. Workflow failed.")
                    raise # Re-raise if all retries fail
                else:
                    logger.info("Retrying workflow...")
                    # Reset relevant project states for retry if needed, or let the next iteration handle it

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

    # Example usage: Replace with your actual LinkedIn profile data or URL
    # For a real run, you'd populate linkedin_profile_data or linkedin_profile_url
    # with actual content or a valid URL.
    # linkedin_data_example = "My LinkedIn profile states I am a Senior Software Engineer with expertise in Python, Machine Learning, and Cloud Computing. I've worked on projects involving natural language processing and distributed systems."
    
    # Using a placeholder URL as Perplexity access might be restricted or require specific setup
    # Make sure your environment variables for Perplexity API key are set if using URL.
    # You might also need to ensure the Perplexity client can access public LinkedIn profiles.
    result = run_blog_creation_workflow(debug=True, linkedin_profile_url="https://www.linkedin.com/in/neerajkumarsinghb/")

    print("\n=== BLOG CREATION RESULTS ===")
    print(f"Selected Topic: {result.get('selected_topic', {}).get('topic', 'N/A')}")
    print(f"Final Score: {result.get('final_score', 'N/A')}/100")
    print(f"Attempts: {result.get('attempts', 'N/A')}")
    print("\n=== FINAL BLOG ===")
    print(result.get("final_blog", "No final blog generated."))
    print("\n=== COMMUNITY RESOURCES ===")
    print(result.get("community_resources", "No community resources found."))
