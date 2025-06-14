"""
Reusable agent definitions for blog creation workflow.
This file can be used if you want to share agents across multiple workflows.
"""

from crewai import Agent
from typing import Any


class BlogAgents:
    """Factory class for creating blog-related agents."""

    @staticmethod
    def create_profile_analyst(llm: Any) -> Agent:
        """Create a LinkedIn profile analyst agent."""
        return Agent(
            role="LinkedIn Profile Analyst",
            goal="Extract expertise and story potential from professional experience",
            backstory=(
                "You are an expert at analyzing professional profiles to find "
                "compelling narratives and technical expertise that can be "
                "transformed into engaging blog content."
            ),
            llm=llm,
            verbose=True,
            allow_delegation=False,
        )

    @staticmethod
    def create_trend_scout(llm: Any) -> Agent:
        """Create a tech trend researcher agent."""
        return Agent(
            role="Tech Trend Researcher",
            goal="Identify trending topics that match user expertise and audience needs",
            backstory=(
                "You are a tech trend analyst who monitors multiple platforms "
                "to find the most engaging and relevant topics for developers."
            ),
            llm=llm,
            verbose=True,
            allow_delegation=False,
        )

    # Add other agent factory methods as needed...
