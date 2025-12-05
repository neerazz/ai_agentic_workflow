"""
Configuration for Blog Creation Agent.

Provides type-safe configuration for all components of the blog creation
agent system with sensible defaults optimized for quality output.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .orchestrator_config import ModelConfig, ModelProvider


class AudienceTier(str, Enum):
    """Target audience tiers for blog content."""
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"


@dataclass
class BlogAgentConfig:
    """Configuration for the Blog Creation Agent."""

    # Model configuration
    model: ModelConfig = field(default_factory=lambda: ModelConfig(
        orchestrator_provider=ModelProvider.GOOGLE,
        orchestrator_model="gemini-1.5-pro",
        planner_provider=ModelProvider.GROQ,
        planner_model="llama-3.1-70b-versatile",
        executor_provider=ModelProvider.GROQ,
        executor_model="llama-3.1-70b-versatile",
    ))

    # Planning and drafting models
    planning_model: str = "gemini-1.5-pro"
    drafting_model: str = "llama-3.1-70b-versatile"
    critique_model: str = "gpt-4o-mini"

    # Token limits
    max_tokens: int = 4000

    # Critique settings
    critique_retries: int = 3
    critique_weights: Dict[str, float] = field(default_factory=lambda: {
        "audience_fit": 0.25,
        "research_rigor": 0.25,
        "trend_alignment": 0.15,
        "tech_choice_balance": 0.15,
        "visual_plan": 0.10,
        "brand_signal": 0.10,
    })

    # Persona and audience settings
    persona_templates_path: Optional[str] = None
    audience_profiles_path: Optional[str] = None
    mentorship_target_distribution: Dict[str, float] = field(default_factory=lambda: {
        "intern": 0.15,
        "junior": 0.25,
        "mid": 0.30,
        "senior": 0.30,
    })

    # Innovation balance
    innovation_ratio: Tuple[float, float] = (0.55, 0.45)  # emerging vs established

    # Brand settings
    brand_pillars: List[str] = field(default_factory=lambda: [
        "Craftsmanship",
        "Clarity",
        "Community"
    ])

    # Trend feeds
    trend_feeds: List[str] = field(default_factory=lambda: [
        "hn",
        "stack_overflow_trends",
        "internal_eng_forums"
    ])

    # Experience library
    experience_library_path: Optional[str] = None

    # Visual settings
    image_density_targets: Dict[str, float] = field(default_factory=lambda: {
        "intern": 1.0,
        "junior": 1.0,
        "mid": 0.75,
        "senior": 0.5,
    })

    # SEO settings
    seo_min_score: float = 0.85

    # Quality thresholds
    min_quality_score: float = 75.0

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        # Validate mentorship distribution sums to 1.0
        total_dist = sum(self.mentorship_target_distribution.values())
        if abs(total_dist - 1.0) > 0.01:
            errors.append(f"Mentorship target distribution must sum to 1.0, got {total_dist}")

        # Validate innovation ratio
        if len(self.innovation_ratio) != 2:
            errors.append("Innovation ratio must be a tuple of 2 values")
        elif abs(sum(self.innovation_ratio) - 1.0) > 0.01:
            errors.append(f"Innovation ratio must sum to 1.0, got {sum(self.innovation_ratio)}")

        # Validate critique weights sum to 1.0
        total_weight = sum(self.critique_weights.values())
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"Critique weights must sum to 1.0, got {total_weight}")

        # Validate model config
        errors.extend(self.model.validate())

        return errors

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return len(self.validate()) == 0


def get_free_tier_blog_config() -> BlogAgentConfig:
    """Get blog agent configuration optimized for free tier usage."""
    return BlogAgentConfig(
        model=ModelConfig(
            orchestrator_provider=ModelProvider.GOOGLE,
            orchestrator_model="gemini-1.5-pro",
            planner_provider=ModelProvider.GROQ,
            planner_model="llama-3.1-70b-versatile",
            executor_provider=ModelProvider.GROQ,
            executor_model="llama-3.1-70b-versatile",
        ),
        planning_model="gemini-1.5-pro",
        drafting_model="llama-3.1-70b-versatile",
        critique_model="gpt-4o-mini",
    )
