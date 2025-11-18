"""
Persona Extractor - Efficiently extracts and stores persona information.

Processes LinkedIn posts, profile, and resume to create a compact,
reusable persona representation that can be used throughout the blog
creation workflow without bloating context windows.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentResult
from ..config import OrchestratorConfig
from ..llm.model_manager import ModelManager
from ..logging import get_logger


@dataclass
class PersonaMemory:
    """
    Efficient memory storage for persona information.
    
    Stores extracted persona data in a compact format that can be
    referenced throughout the blog creation process without including
    all raw LinkedIn data in every prompt.
    """
    
    # Core identity
    role: str = ""
    expertise_areas: List[str] = field(default_factory=list)
    years_experience: Optional[int] = None
    
    # Voice and style (extracted from posts)
    writing_style: Dict[str, Any] = field(default_factory=dict)
    common_phrases: List[str] = field(default_factory=list)
    tone_markers: List[str] = field(default_factory=list)
    storytelling_patterns: List[str] = field(default_factory=list)
    
    # Technical expertise (from profile/resume)
    technical_skills: Dict[str, int] = field(default_factory=dict)  # skill -> years
    career_highlights: List[Dict[str, Any]] = field(default_factory=list)
    project_experiences: List[Dict[str, Any]] = field(default_factory=list)
    
    # Content preferences (from posts analysis)
    preferred_topics: List[str] = field(default_factory=list)
    engagement_patterns: Dict[str, Any] = field(default_factory=dict)
    audience_connection_style: str = ""
    
    # Brand and values
    brand_pillars: List[str] = field(default_factory=list)
    core_values: List[str] = field(default_factory=list)
    mentorship_style: str = ""
    
    # Compact summaries (for context efficiency)
    voice_summary: str = ""  # 2-3 sentence summary of writing voice
    expertise_summary: str = ""  # 2-3 sentence summary of expertise
    story_bank_summary: str = ""  # Summary of available stories
    
    # Metadata
    extraction_date: str = field(default_factory=lambda: datetime.now().isoformat())
    source_files: List[str] = field(default_factory=list)
    
    def to_compact_dict(self) -> Dict[str, Any]:
        """Convert to compact dictionary for prompts (excludes raw data)."""
        return {
            "role": self.role,
            "expertise_areas": self.expertise_areas,
            "years_experience": self.years_experience,
            "writing_style": self.writing_style,
            "voice_summary": self.voice_summary,
            "expertise_summary": self.expertise_summary,
            "story_bank_summary": self.story_bank_summary,
            "technical_skills": self.technical_skills,
            "preferred_topics": self.preferred_topics,
            "brand_pillars": self.brand_pillars,
            "core_values": self.core_values,
            "mentorship_style": self.mentorship_style,
            "audience_connection_style": self.audience_connection_style,
        }
    
    def to_full_dict(self) -> Dict[str, Any]:
        """Convert to full dictionary with all data."""
        return asdict(self)
    
    def save(self, filepath: str):
        """Save persona memory to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_full_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, filepath: str) -> 'PersonaMemory':
        """Load persona memory from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)


class PersonaExtractor(BaseAgent):
    """
    Extracts persona information from LinkedIn posts, profile, and resume.
    
    Uses efficient extraction to create a compact PersonaMemory that can
    be reused throughout the blog creation process.
    """
    
    def __init__(
        self,
        config: Optional[OrchestratorConfig] = None,
        name: Optional[str] = None
    ):
        """Initialize Persona Extractor."""
        if config is None:
            from ..config import get_free_tier_config
            config = get_free_tier_config()
        
        super().__init__(config, name or "PersonaExtractor")
        self.logger = get_logger(__name__)
    
    def execute(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Extract persona from LinkedIn data.
        
        Args:
            user_input: Not used directly
            context: Should contain:
                - linkedin_posts: List of LinkedIn post texts
                - linkedin_profile: LinkedIn profile text
                - resume: Optional resume text
        
        Returns:
            AgentResult with PersonaMemory in output
        """
        if not context:
            return AgentResult(
                success=False,
                output=None,
                error="Context required with linkedin_posts and/or linkedin_profile"
            )
        
        try:
            linkedin_posts = context.get("linkedin_posts", [])
            linkedin_profile = context.get("linkedin_profile", "")
            resume = context.get("resume", "")
            
            if not linkedin_posts and not linkedin_profile:
                return AgentResult(
                    success=False,
                    output=None,
                    error="At least linkedin_posts or linkedin_profile required"
                )
            
            persona_memory = self._extract_persona(
                linkedin_posts=linkedin_posts,
                linkedin_profile=linkedin_profile,
                resume=resume
            )
            
            return AgentResult(
                success=True,
                output=persona_memory,
                metadata={
                    "posts_analyzed": len(linkedin_posts),
                    "has_profile": bool(linkedin_profile),
                    "has_resume": bool(resume),
                }
            )
        
        except Exception as e:
            return self.handle_error(e)
    
    def _extract_persona(
        self,
        linkedin_posts: List[str],
        linkedin_profile: str,
        resume: str
    ) -> PersonaMemory:
        """Extract persona information efficiently."""
        self.logger.info("Extracting persona from LinkedIn data", metadata={
            "posts_count": len(linkedin_posts),
            "profile_length": len(linkedin_profile),
            "resume_length": len(resume),
        })
        
        # Step 1: Extract core identity from profile/resume
        core_identity = self._extract_core_identity(linkedin_profile, resume)
        
        # Step 2: Extract voice and style from posts (most recent first)
        voice_data = self._extract_voice_style(linkedin_posts)
        
        # Step 3: Extract technical expertise from profile/resume
        technical_data = self._extract_technical_expertise(linkedin_profile, resume)
        
        # Step 4: Extract content preferences from posts
        content_prefs = self._extract_content_preferences(linkedin_posts)
        
        # Step 5: Extract brand and values
        brand_data = self._extract_brand_values(linkedin_posts, linkedin_profile)
        
        # Step 6: Create compact summaries
        summaries = self._create_summaries(core_identity, voice_data, technical_data)
        
        # Combine into PersonaMemory
        persona = PersonaMemory(
            role=core_identity.get("role", ""),
            expertise_areas=core_identity.get("expertise_areas", []),
            years_experience=core_identity.get("years_experience"),
            writing_style=voice_data.get("style", {}),
            common_phrases=voice_data.get("common_phrases", []),
            tone_markers=voice_data.get("tone_markers", []),
            storytelling_patterns=voice_data.get("storytelling_patterns", []),
            technical_skills=technical_data.get("skills", {}),
            career_highlights=technical_data.get("highlights", []),
            project_experiences=technical_data.get("projects", []),
            preferred_topics=content_prefs.get("topics", []),
            engagement_patterns=content_prefs.get("engagement", {}),
            audience_connection_style=content_prefs.get("connection_style", ""),
            brand_pillars=brand_data.get("pillars", []),
            core_values=brand_data.get("values", []),
            mentorship_style=brand_data.get("mentorship_style", ""),
            voice_summary=summaries.get("voice", ""),
            expertise_summary=summaries.get("expertise", ""),
            story_bank_summary=summaries.get("stories", ""),
            source_files=["linkedin_posts", "linkedin_profile"] + (["resume"] if resume else []),
        )
        
        self.logger.info("Persona extraction completed", metadata={
            "expertise_areas": len(persona.expertise_areas),
            "technical_skills": len(persona.technical_skills),
            "career_highlights": len(persona.career_highlights),
        })
        
        return persona
    
    def _extract_core_identity(self, profile: str, resume: str) -> Dict[str, Any]:
        """Extract core identity (role, experience, expertise areas)."""
        # Use most recent/relevant data first
        text = profile if profile else resume
        if not text:
            return {}
        
        # Limit text to avoid token bloat - use first 2000 chars (usually has key info)
        text_sample = text[:2000] if len(text) > 2000 else text
        
        prompt = f"""Extract core professional identity from this profile/resume.

Text: {text_sample}

Extract:
- role: Current or most recent job title
- expertise_areas: Top 5-7 areas of expertise (e.g., ["Microservices", "Kubernetes", "Python"])
- years_experience: Total years of professional experience (estimate if not explicit)

Return as JSON:
{{
    "role": "...",
    "expertise_areas": ["...", "..."],
    "years_experience": X
}}"""

        try:
            response = self.model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.warning(f"Error extracting core identity: {e}")
            return {}
    
    def _extract_voice_style(self, posts: List[str]) -> Dict[str, Any]:
        """Extract writing voice and style from LinkedIn posts."""
        if not posts:
            return {}
        
        # Use most recent posts (last 10) and sample them intelligently
        recent_posts = posts[-10:] if len(posts) > 10 else posts
        
        # Create representative sample (don't dump all posts)
        # Take first 500 chars of each post to stay within token limits
        post_samples = []
        for i, post in enumerate(recent_posts):
            sample = post[:500] if len(post) > 500 else post
            post_samples.append(f"Post {i+1}: {sample}")
        
        posts_text = "\n\n".join(post_samples)
        
        prompt = f"""Analyze writing voice and style from these LinkedIn posts.

Posts:
{posts_text}

Extract:
- style: Writing style characteristics (conversational, technical, storytelling, etc.)
- common_phrases: 5-7 phrases or expressions frequently used
- tone_markers: Words/phrases that indicate tone (e.g., "pragmatic", "encouraging")
- storytelling_patterns: How stories are told (e.g., "struggle-to-success", "lesson-learned")

Return as JSON:
{{
    "style": {{"primary": "...", "characteristics": ["...", "..."]}},
    "common_phrases": ["...", "..."],
    "tone_markers": ["...", "..."],
    "storytelling_patterns": ["...", "..."]
}}"""

        try:
            response = self.model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.warning(f"Error extracting voice style: {e}")
            return {}
    
    def _extract_technical_expertise(self, profile: str, resume: str) -> Dict[str, Any]:
        """Extract technical skills and career highlights."""
        text = profile if profile else resume
        if not text:
            return {}
        
        # Focus on work experience and skills sections
        # Use first 3000 chars (usually contains work experience)
        text_sample = text[:3000] if len(text) > 3000 else text
        
        prompt = f"""Extract technical expertise and career highlights.

Text: {text_sample}

Extract:
- skills: Dictionary of technology -> years of experience (e.g., {{"Python": 5, "Kubernetes": 3}})
- highlights: List of 3-5 major career achievements/highlights
- projects: List of 3-5 notable projects with brief descriptions

Return as JSON:
{{
    "skills": {{"technology": years}},
    "highlights": [
        {{"title": "...", "description": "...", "technologies": ["..."]}}
    ],
    "projects": [
        {{"name": "...", "description": "...", "technologies": ["..."]}}
    ]
}}"""

        try:
            response = self.model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.warning(f"Error extracting technical expertise: {e}")
            return {}
    
    def _extract_content_preferences(self, posts: List[str]) -> Dict[str, Any]:
        """Extract content preferences and engagement patterns."""
        if not posts:
            return {}
        
        # Analyze post topics and engagement style
        recent_posts = posts[-10:] if len(posts) > 10 else posts
        post_samples = [post[:300] for post in recent_posts]
        posts_text = "\n\n".join([f"Post {i+1}: {p}" for i, p in enumerate(post_samples)])
        
        prompt = f"""Analyze content preferences from LinkedIn posts.

Posts:
{posts_text}

Extract:
- topics: List of 5-7 topics frequently written about
- engagement: How author engages with audience (e.g., "asks questions", "shares stories")
- connection_style: How author connects with readers (e.g., "mentor", "peer", "expert")

Return as JSON:
{{
    "topics": ["...", "..."],
    "engagement": {{"style": "...", "techniques": ["..."]}},
    "connection_style": "..."
}}"""

        try:
            response = self.model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.warning(f"Error extracting content preferences: {e}")
            return {}
    
    def _extract_brand_values(self, posts: List[str], profile: str) -> Dict[str, Any]:
        """Extract brand pillars and core values."""
        # Combine insights from both posts and profile
        text_parts = []
        if posts:
            recent_posts = posts[-5:] if len(posts) > 5 else posts
            text_parts.append("Recent Posts:\n" + "\n\n".join([p[:200] for p in recent_posts]))
        if profile:
            text_parts.append("Profile:\n" + profile[:1000])
        
        combined_text = "\n\n".join(text_parts)
        
        prompt = f"""Extract brand values and mentorship style.

{combined_text}

Extract:
- pillars: 3-5 brand pillars or core values (e.g., ["Craftsmanship", "Clarity", "Community"])
- values: List of personal/professional values
- mentorship_style: How author mentors/teaches (e.g., "pragmatic", "encouraging", "hands-on")

Return as JSON:
{{
    "pillars": ["...", "..."],
    "values": ["...", "..."],
    "mentorship_style": "..."
}}"""

        try:
            response = self.model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.warning(f"Error extracting brand values: {e}")
            return {}
    
    def _create_summaries(
        self,
        core_identity: Dict[str, Any],
        voice_data: Dict[str, Any],
        technical_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Create compact summaries for efficient context usage."""
        prompt = f"""Create compact summaries for persona memory.

Core Identity: {json.dumps(core_identity)}
Voice Data: {json.dumps(voice_data)}
Technical Data: {json.dumps(technical_data)}

Create three 2-3 sentence summaries:
1. voice_summary: Writing voice and style
2. expertise_summary: Technical expertise and experience
3. story_bank_summary: Available stories and experiences for blog content

Return as JSON:
{{
    "voice": "...",
    "expertise": "...",
    "stories": "..."
}}"""

        try:
            response = self.model_manager.planner_generate(prompt)
            summaries = self._safe_json_parse(response.content, {})
            return {
                "voice": summaries.get("voice", ""),
                "expertise": summaries.get("expertise", ""),
                "stories": summaries.get("stories", ""),
            }
        except Exception as e:
            self.logger.warning(f"Error creating summaries: {e}")
            return {
                "voice": "Professional technical writer",
                "expertise": "Software engineering",
                "stories": "Career experiences and project learnings",
            }
    
    def _safe_json_parse(self, content: str, default: Any = {}) -> Any:
        """Safely parse JSON from LLM response."""
        try:
            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                if len(lines) > 2:
                    content = "\n".join(lines[1:-1])
            
            if content.startswith("{") or content.startswith("["):
                return json.loads(content)
            
            import re
            json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
            matches = re.findall(json_pattern, content, re.DOTALL)
            if matches:
                return json.loads(max(matches, key=len))
            
            return default
        except Exception as e:
            self.logger.warning(f"JSON parse error: {e}")
            return default
