"""
Blog Creation Agent - Multi-Audience Editorial Studio

A comprehensive AI agent for creating high-quality technical blog posts
from the perspective of a principal software engineer, with support for
multiple audience tiers and sophisticated editorial workflows.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_agent import BaseAgent, AgentResult
from ..config import OrchestratorConfig
from ..config.blog_agent_config import BlogAgentConfig, get_free_tier_blog_config
from ..llm.model_manager import ModelManager
from ..logging import get_logger, trace_context


@dataclass
class BlogBrief:
    """Input brief for blog creation."""
    persona: Optional[str] = None
    topic: Optional[str] = None
    goal: Optional[str] = None
    voice: Optional[str] = None
    target_audience: Optional[List[str]] = None
    brand_pillars: Optional[List[str]] = None
    user_input: Optional[str] = None  # Optional free-form input


@dataclass
class BlogDeliverable:
    """Complete blog deliverable package."""
    packaged_post: str  # Final markdown blog post
    title: str
    meta_description: str
    seo_keywords: List[str]
    quality_report: Dict[str, Any]
    visual_storyboard: Dict[str, Any]
    promo_bundle: Dict[str, Any]
    knowledge_transfer_kit: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


class BlogCreationAgent(BaseAgent):
    """
    Principal Engineer Blog Creation Agent.

    Creates persona-aware, multi-audience technical blog posts with
    sophisticated editorial workflows, critique loops, and quality gates.
    """

    def __init__(
        self,
        config: Optional[BlogAgentConfig] = None,
        orchestrator_config: Optional[OrchestratorConfig] = None,
        name: Optional[str] = None
    ):
        """
        Initialize Blog Creation Agent.

        Args:
            config: Blog agent specific configuration.
            orchestrator_config: Base orchestrator configuration (for ModelManager).
            name: Agent name.
        """
        # Use orchestrator config for ModelManager, or create default
        if orchestrator_config is None:
            from ..config import get_free_tier_config
            orchestrator_config = get_free_tier_config()

        super().__init__(orchestrator_config, name or "BlogCreationAgent")

        # Blog-specific config
        self.blog_config = config or get_free_tier_blog_config()

        # Validate blog config
        if not self.blog_config.is_valid():
            errors = self.blog_config.validate()
            self.logger.error(f"Invalid blog config: {errors}")
            raise ValueError(f"Invalid blog configuration: {errors}")

        # Initialize specialized model manager for blog creation
        self.blog_model_manager = ModelManager(self.blog_config.model)

        self.logger.info("BlogCreationAgent initialized", metadata={
            "planning_model": self.blog_config.planning_model,
            "drafting_model": self.blog_config.drafting_model,
            "critique_model": self.blog_config.critique_model,
        })

    def _safe_json_parse(self, content: str, default: Any = {}) -> Any:
        """
        Safely parse JSON from LLM response with fallback.
        
        Args:
            content: Response content from LLM
            default: Default value if parsing fails
            
        Returns:
            Parsed JSON or default value
        """
        try:
            content = content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                # Remove first line (```json or ```) and last line (```)
                if len(lines) > 2:
                    content = "\n".join(lines[1:-1])
                elif len(lines) == 2:
                    content = lines[1]
            
            # Try direct parse
            if content.startswith("{") or content.startswith("["):
                return json.loads(content)
            
            # Try to find JSON object/array in content
            import re
            # Match JSON object
            json_obj_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
            json_arr_pattern = r"\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]"
            
            matches = re.findall(json_obj_pattern, content, re.DOTALL)
            if not matches:
                matches = re.findall(json_arr_pattern, content, re.DOTALL)
            
            if matches:
                # Try to parse the largest match (likely most complete)
                largest_match = max(matches, key=len)
                return json.loads(largest_match)
            
            # Last resort: try to extract anything that looks like JSON
            start_idx = content.find("{")
            if start_idx == -1:
                start_idx = content.find("[")
            
            if start_idx != -1:
                # Find matching closing brace/bracket
                bracket = content[start_idx]
                close_bracket = "}" if bracket == "{" else "]"
                depth = 0
                for i in range(start_idx, len(content)):
                    if content[i] == bracket:
                        depth += 1
                    elif content[i] == close_bracket:
                        depth -= 1
                        if depth == 0:
                            return json.loads(content[start_idx:i+1])
            
            # If all else fails, return default
            self.logger.warning(f"Could not parse JSON from content: {content[:200]}...")
            return default
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON decode error: {e}, content: {content[:200]}...")
            return default
        except Exception as e:
            self.logger.warning(f"Error parsing JSON: {e}")
            return default

    def execute(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        """
        Execute blog creation workflow.

        Args:
            user_input: User's input (can be topic, persona, or free-form request).
            context: Optional context with BlogBrief or other structured data.

        Returns:
            AgentResult with BlogDeliverable in output field.
        """
        if not self.validate_input(user_input):
            return self.handle_error(ValueError("Invalid user input"))

        try:
            with trace_context("blog_creation_execute"):
                # Parse input into BlogBrief
                brief = self._parse_input(user_input, context)

                # Execute the blog creation pipeline
                deliverable = self._create_blog(brief)

                return AgentResult(
                    success=True,
                    output=deliverable,
                    metadata={
                        "brief": brief.__dict__,
                        "quality_score": deliverable.quality_report.get("final_score", 0),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        except Exception as e:
            return self.handle_error(e)

    def _parse_input(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]]
    ) -> BlogBrief:
        """Parse user input into structured BlogBrief."""
        # If context contains a BlogBrief, use it
        if context and "brief" in context:
            brief_data = context["brief"]
            if isinstance(brief_data, BlogBrief):
                return brief_data
            elif isinstance(brief_data, dict):
                return BlogBrief(**brief_data)

        # Otherwise, parse from user input
        # Use LLM to extract structured information from free-form input
        parse_prompt = f"""Parse the following user input and extract blog creation requirements.

User Input: {user_input}

Extract the following information:
- persona: The author's persona or role (e.g., "Principal Software Engineer")
- topic: The blog topic or subject
- goal: The goal of the blog (e.g., "teach", "inspire", "share experience")
- voice: Writing voice/style preferences
- target_audience: List of target audiences (intern, junior, mid, senior)
- brand_pillars: Key brand values or pillars

Return as JSON:
{{
    "persona": "...",
    "topic": "...",
    "goal": "...",
    "voice": "...",
    "target_audience": ["intern", "junior"],
    "brand_pillars": ["Craftsmanship", "Clarity"]
}}

If information is not provided, use null or empty values."""

        try:
            response = self.blog_model_manager.planner_generate(parse_prompt)
            # Try to extract JSON from response
            content = response.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
            
            # Try to find JSON object
            json_match = None
            if content.startswith("{"):
                json_match = content
            else:
                # Try to find JSON in the content
                import re
                json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
                matches = re.findall(json_pattern, content, re.DOTALL)
                if matches:
                    json_match = matches[-1]  # Take the last (likely most complete) match
            
            if json_match:
                parsed = json.loads(json_match)
                return BlogBrief(
                    persona=parsed.get("persona"),
                    topic=parsed.get("topic"),
                    goal=parsed.get("goal"),
                    voice=parsed.get("voice"),
                    target_audience=parsed.get("target_audience", []),
                    brand_pillars=parsed.get("brand_pillars", []),
                    user_input=user_input,
                )
            else:
                raise ValueError("No JSON found in response")
        except Exception as e:
            self.logger.warning(f"Failed to parse input with LLM: {e}, using defaults")
            # Fallback: create brief with user input as topic
            return BlogBrief(
                topic=user_input if user_input else "Technical blog post",
                user_input=user_input,
            )

    def _create_blog(self, brief: BlogBrief) -> BlogDeliverable:
        """
        Execute the complete blog creation pipeline.

        Implements the 16-stage workflow from the README.
        """
        self.logger.info("Starting blog creation pipeline", metadata={
            "topic": brief.topic,
            "persona": brief.persona,
        })

        # Stage 1-2: Persona & Audience Analysis
        persona_sheet = self._create_persona_sheet(brief)
        audience_trends = self._analyze_audience_trends(brief, persona_sheet)

        # Stage 3-4: Experience Alignment & Depth Planning
        experience_alignment = self._align_experience(brief, persona_sheet)
        depth_guardrails = self._plan_depth_guardrails(brief, experience_alignment)

        # Stage 5-6: Strategy & Audience Ladder
        strategy = self._compose_strategy(brief, persona_sheet, audience_trends)
        audience_matrix = self._build_audience_matrix(brief, strategy)

        # Stage 7-8: Topic Routing & Series Planning
        topic_decision = self._route_topic(brief, audience_matrix, strategy)
        series_blueprint = self._plan_series(brief, topic_decision)

        # Stage 9: Innovation Balance
        innovation_plan = self._calibrate_innovation_balance(brief, strategy)

        # Stage 10: Research & Facts
        research_data = self._conduct_research(brief, strategy, innovation_plan)

        # Stage 11: Outline Creation
        outline = self._weave_outline(brief, strategy, research_data, series_blueprint)
        
        # Ensure outline has sections
        if "sections" not in outline or not outline.get("sections"):
            self.logger.warning("Outline missing sections, creating default structure")
            outline["sections"] = [
                {"title": "Introduction", "objective": "Introduce the topic"},
                {"title": "Main Content", "objective": "Deep dive into the topic"},
                {"title": "Conclusion", "objective": "Wrap up and provide takeaways"}
            ]

        # Stage 12: Section Enhancement
        enhanced_sections = self._enhance_sections(outline, research_data, audience_matrix)

        # Stage 13: Critique & Decision
        critique_result = self._critique_content(enhanced_sections, brief, persona_sheet)
        approved_sections = self._gate_decision(critique_result, enhanced_sections)

        # Stage 14: Drafting & Voice
        draft = self._craft_draft(approved_sections, persona_sheet, strategy)
        polished_draft = self._polish_voice(draft, persona_sheet, brief)

        # Stage 15: SEO & Brand
        seo_pack = self._orchestrate_seo(polished_draft, brief)
        brand_signals = self._track_brand_signals(polished_draft, brief, persona_sheet)

        # Stage 16: Visual Storytelling
        visual_storyboard = self._create_visual_storyboard(outline, approved_sections, brief)

        # Final Assembly
        deliverable = self._assemble_deliverable(
            polished_draft,
            seo_pack,
            brand_signals,
            visual_storyboard,
            critique_result,
            brief
        )

        self.logger.info("Blog creation pipeline completed", metadata={
            "quality_score": deliverable.quality_report.get("final_score", 0),
        })

        return deliverable

    # Stage implementations (simplified for now, can be expanded)
    def _create_persona_sheet(self, brief: BlogBrief) -> Dict[str, Any]:
        """Stage 1: PersonaArchitect - Create persona sheet."""
        prompt = f"""Create a detailed persona sheet for a blog author.

Persona: {brief.persona or "Principal Software Engineer"}
Goal: {brief.goal or "Share technical knowledge and mentor developers"}
Voice: {brief.voice or "Pragmatic mentor, data-backed, grounded optimism"}

Generate a persona sheet with:
- tone and style preferences
- north-star principles
- mentorship cadence
- brand guardrails
- CTA preferences
- taboo claims to avoid

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error creating persona sheet: {e}")
            return {
                "tone": brief.voice or "Pragmatic mentor",
                "persona": brief.persona or "Principal Software Engineer",
                "goal": brief.goal or "Share technical knowledge"
            }

    def _analyze_audience_trends(self, brief: BlogBrief, persona_sheet: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: AudienceTrendRadar - Analyze audience trends."""
        prompt = f"""Analyze current trends for software engineering audiences.

Topic: {brief.topic or "General software engineering"}
Target Audiences: {brief.target_audience or ["junior", "mid", "senior"]}

Identify:
- What each audience tier currently cares about
- Frustration points
- Trend saturation levels
- Engagement opportunities

Return as JSON with per-cohort trend maps."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _align_experience(self, brief: BlogBrief, persona_sheet: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 3: ExperienceAligner - Align with authentic experience."""
        prompt = f"""Align the blog topic with authentic principal engineer experience.

Topic: {brief.topic}
Persona: {brief.persona}

Identify:
- Authentic battle-tested stories
- Shipped systems and projects
- Unique point of view
- Credibility markers

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _plan_depth_guardrails(self, brief: BlogBrief, experience: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 4: DepthCompass - Plan depth guardrails."""
        prompt = f"""Plan depth guardrails for the blog content.

Topic: {brief.topic}
Target Audiences: {brief.target_audience}

Define per-section depth levels:
- Conceptual depth
- Design depth
- Code depth
- Operations depth
- Business impact depth

Ensure interns don't drown while seniors get rigor.

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _compose_strategy(self, brief: BlogBrief, persona_sheet: Dict[str, Any], trends: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 5: StrategyComposer - Compose blog strategy."""
        prompt = f"""Compose the blog strategy and thesis.

Topic: {brief.topic}
Persona: {brief.persona}
Trends: {json.dumps(trends)}

Define:
- Core thesis
- Narrative hook
- War stories to include
- Success KPIs
- Anti-patterns to address

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _build_audience_matrix(self, brief: BlogBrief, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 6: AudienceLens - Build audience comprehension matrix."""
        prompt = f"""Build audience comprehension matrix.

Strategy: {json.dumps(strategy)}
Target Audiences: {brief.target_audience or ["intern", "junior", "mid", "senior"]}

Create matrix with:
- Per-cohort learning objectives
- Format requirements
- Comprehension levels
- Multi-resolution summaries

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _route_topic(self, brief: BlogBrief, audience_matrix: Dict[str, Any], strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 7: TopicRouter - Route topic to appropriate audiences."""
        prompt = f"""Route the topic to appropriate audiences.

Topic: {brief.topic}
Audience Matrix: {json.dumps(audience_matrix)}

Decide:
- Single audience or multi-audience
- Need for sidebars
- Audience gating requirements

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _plan_series(self, brief: BlogBrief, topic_decision: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 8: BlogSeriesPlanner - Plan single vs multi-blog series."""
        prompt = f"""Plan blog series structure.

Topic: {brief.topic}
Topic Decision: {json.dumps(topic_decision)}

Decide:
- Single comprehensive post or multi-part series
- If series: high-level sections per installment
- Release order
- Cross-linking strategy

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _calibrate_innovation_balance(self, brief: BlogBrief, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 9: TechLandscapeCalibrator - Calibrate innovation balance."""
        prompt = f"""Calibrate innovation balance.

Topic: {brief.topic}
Strategy: {json.dumps(strategy)}
Innovation Ratio: {self.blog_config.innovation_ratio}

Plan:
- Emerging vs established tech ratio
- Bridge paragraphs connecting new to reliable
- Section badges (Emerging/Established/Hybrid)

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _conduct_research(self, brief: BlogBrief, strategy: Dict[str, Any], innovation_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 10: ResearchScout + FactSentinel - Conduct research."""
        prompt = f"""Conduct research and fact-checking.

Topic: {brief.topic}
Strategy: {json.dumps(strategy)}

Gather:
- Benchmarks and RFC links
- Whitepapers and release notes
- Fact cards with citations
- Threat models
- Architecture references

Return as JSON with fact cards."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _weave_outline(self, brief: BlogBrief, strategy: Dict[str, Any], research: Dict[str, Any], series: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 11: OutlineWeaver - Create blog outline."""
        prompt = f"""Create comprehensive blog outline.

Topic: {brief.topic}
Strategy: {json.dumps(strategy)}
Research: {json.dumps(research)}
Series Plan: {json.dumps(series)}

Create hierarchical outline with:
- Section titles
- Per-section objectives
- CTA placements
- Asset wishlist
- Audience tags

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _enhance_sections(self, outline: Dict[str, Any], research: Dict[str, Any], audience_matrix: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Stage 12: SectionEnhancer - Enhance each section."""
        sections = outline.get("sections", [])
        if not sections:
            self.logger.warning("No sections found in outline, creating default section")
            sections = [{"title": "Introduction", "content": "Introduction to the topic"}]
        
        enhanced = []

        for section in sections:
            prompt = f"""Enhance blog section with depth and engagement.

Section: {json.dumps(section)}
Research: {json.dumps(research)}
Audience Matrix: {json.dumps(audience_matrix)}

Add:
- Analogies
- Depth markers
- Questions for peers
- Recommended visuals
- Code examples

Return enhanced section as JSON."""

            try:
                response = self.blog_model_manager.planner_generate(prompt)
                enhanced_section = self._safe_json_parse(response.content, section)
                enhanced.append(enhanced_section)
            except Exception as e:
                self.logger.warning(f"Error enhancing section: {e}, using original")
                enhanced.append(section)

        return enhanced

    def _critique_content(self, sections: List[Dict[str, Any]], brief: BlogBrief, persona_sheet: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 13: CritiqueCouncil - Critique content."""
        prompt = f"""Critique blog sections for quality.

Sections: {json.dumps(sections)}
Persona Sheet: {json.dumps(persona_sheet)}
Brief: {json.dumps(brief.__dict__)}

Evaluate on:
- Audience fit (25%)
- Research rigor (25%)
- Trend alignment (15%)
- Tech choice balance (15%)
- Visual plan (10%)
- Brand signal (10%)

Return critique scores and feedback as JSON."""

        # Use critique model (typically GPT-4o-mini for cost efficiency)
        # Map critique_model string to provider
        from ..config import ModelProvider
        critique_model_lower = self.blog_config.critique_model.lower()
        
        if 'gpt' in critique_model_lower or 'openai' in critique_model_lower:
            provider = ModelProvider.OPENAI
        elif 'gemini' in critique_model_lower or 'google' in critique_model_lower:
            provider = ModelProvider.GOOGLE
        elif 'llama' in critique_model_lower or 'groq' in critique_model_lower:
            provider = ModelProvider.GROQ
        elif 'claude' in critique_model_lower or 'anthropic' in critique_model_lower:
            provider = ModelProvider.ANTHROPIC
        else:
            # Default to planner provider
            provider = self.blog_config.model.planner_provider
        
        try:
            response = self.blog_model_manager.generate_with_provider(
                provider_name=provider,
                model=self.blog_config.critique_model,
                prompt=prompt,
                temperature=0.3,
            )
            return self._safe_json_parse(response.content, {"overall_score": 0, "feedback": "Critique parsing failed"})
        except Exception as e:
            self.logger.error(f"Error in critique: {e}")
            return {"overall_score": 50, "feedback": f"Critique failed: {str(e)}"}

    def _gate_decision(self, critique: Dict[str, Any], sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Stage 13: DecisionGater - Make accept/revise decisions."""
        overall_score = critique.get("overall_score", 0)

        if overall_score >= self.blog_config.min_quality_score:
            self.logger.info(f"Content approved with score {overall_score}")
            return sections
        else:
            self.logger.warning(f"Content below threshold ({overall_score} < {self.blog_config.min_quality_score})")
            # In a full implementation, would trigger revision loop
            return sections  # For now, proceed with current sections

    def _craft_draft(self, sections: List[Dict[str, Any]], persona_sheet: Dict[str, Any], strategy: Dict[str, Any]) -> str:
        """Stage 14: DraftCrafter - Write the blog draft."""
        # Limit JSON size to avoid token limits
        sections_summary = json.dumps(sections[:5]) if len(sections) > 5 else json.dumps(sections)
        persona_summary = json.dumps({k: v for k, v in list(persona_sheet.items())[:5]})
        strategy_summary = json.dumps({k: v for k, v in list(strategy.items())[:5]})
        
        prompt = f"""Write the complete blog post.

Sections: {sections_summary}
Persona Sheet: {persona_summary}
Strategy: {strategy_summary}

Write a complete, engaging blog post in markdown format.
Target: 2000-3000 words.
Include code examples, personal anecdotes, and clear explanations.
Follow the persona voice and strategy."""

        try:
            response = self.blog_model_manager.executor_generate(prompt, temperature=0.7)
            return response.content
        except Exception as e:
            self.logger.error(f"Error crafting draft: {e}")
            # Fallback: create simple draft from sections
            draft = "# Blog Post\n\n"
            for section in sections:
                draft += f"## {section.get('title', 'Section')}\n\n"
                draft += f"{section.get('content', section.get('objective', ''))}\n\n"
            return draft

    def _polish_voice(self, draft: str, persona_sheet: Dict[str, Any], brief: BlogBrief) -> str:
        """Stage 14: VoiceGuardian - Polish voice and style."""
        # Limit draft preview to avoid token limits
        draft_preview = draft[:2000] + "..." if len(draft) > 2000 else draft
        persona_summary = json.dumps({k: v for k, v in list(persona_sheet.items())[:3]})
        
        prompt = f"""Polish the blog post voice and style.

Draft: {draft_preview}
Persona Sheet: {persona_summary}
Voice: {brief.voice or "Pragmatic mentor"}

Ensure:
- Consistent voice throughout
- Scannable structure (H2/H3 cadence)
- Appropriate code-to-text ratio
- Inclusive language
- CTA placement

Return polished markdown."""

        try:
            response = self.blog_model_manager.executor_generate(prompt, temperature=0.5)
            return response.content
        except Exception as e:
            self.logger.warning(f"Error polishing voice: {e}, returning original draft")
            return draft

    def _orchestrate_seo(self, draft: str, brief: BlogBrief) -> Dict[str, Any]:
        """Stage 15: SEOOrchestrator - Optimize for SEO."""
        prompt = f"""Create SEO optimization package.

Draft: {draft[:1500]}...
Topic: {brief.topic}

Generate:
- SEO-optimized title
- Meta description
- Keyword list
- SERP intent coverage
- Internal/external link suggestions
- Snippet-ready highlights

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _track_brand_signals(self, draft: str, brief: BlogBrief, persona_sheet: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 15: BrandSignalTracker - Track brand signals."""
        brand_pillars = brief.brand_pillars or self.blog_config.brand_pillars

        prompt = f"""Analyze brand signal strength.

Draft: {draft[:1500]}...
Brand Pillars: {brand_pillars}
Persona: {brief.persona}

Score how well each section reinforces brand pillars.
Identify:
- Trust checklist compliance
- Community engagement hooks
- Knowledge-sharing assets

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _create_visual_storyboard(self, outline: Dict[str, Any], sections: List[Dict[str, Any]], brief: BlogBrief) -> Dict[str, Any]:
        """Stage 16: VisualStoryboarder - Create visual storyboard."""
        prompt = f"""Create visual storyboard.

Outline: {json.dumps(outline)}
Sections: {json.dumps(sections[:3])}  # Limit for token efficiency
Image Density Targets: {self.blog_config.image_density_targets}

Plan:
- Images per section
- Image descriptions
- Diagram types needed
- Style guidance
- Accessibility notes

Return as JSON."""

        try:
            response = self.blog_model_manager.planner_generate(prompt)
            return self._safe_json_parse(response.content, {})
        except Exception as e:
            self.logger.error(f"Error in stage: {e}")
            return {}

    def _assemble_deliverable(
        self,
        draft: str,
        seo_pack: Dict[str, Any],
        brand_signals: Dict[str, Any],
        visual_storyboard: Dict[str, Any],
        critique_result: Dict[str, Any],
        brief: BlogBrief
    ) -> BlogDeliverable:
        """Stage 16: DeliverableAssembler - Assemble final deliverable."""
        # Create promo bundle
        promo_prompt = f"""Create promotional content bundle.

Blog: {draft[:1000]}...
Topic: {brief.topic}

Generate:
- TL;DR summary
- Tweet thread (6 tweets)
- LinkedIn hook
- Newsletter blurb
- "Mentor minute" video script seed

Return as JSON."""

        try:
            promo_response = self.blog_model_manager.planner_generate(promo_prompt)
            promo_bundle = self._safe_json_parse(promo_response.content, {})
        except Exception as e:
            self.logger.error(f"Error creating promo bundle: {e}")
            promo_bundle = {}

        # Create knowledge transfer kit
        kit_prompt = f"""Create knowledge transfer kit.

Blog: {draft[:1000]}...
Topic: {brief.topic}

Generate:
- Action items for readers
- Mentorship prompts
- Code walkthrough cues
- Discussion questions

Return as JSON."""

        try:
            kit_response = self.blog_model_manager.planner_generate(kit_prompt)
            knowledge_kit = self._safe_json_parse(kit_response.content, {})
        except Exception as e:
            self.logger.error(f"Error creating knowledge kit: {e}")
            knowledge_kit = {}

        # Calculate final quality score
        final_score = critique_result.get("overall_score", 0)

        quality_report = {
            "final_score": final_score,
            "critique_details": critique_result,
            "seo_score": seo_pack.get("seo_score", 0),
            "brand_score": brand_signals.get("overall_score", 0),
        }

        return BlogDeliverable(
            packaged_post=draft,
            title=seo_pack.get("title", brief.topic or "Blog Post"),
            meta_description=seo_pack.get("meta_description", ""),
            seo_keywords=seo_pack.get("keywords", []),
            quality_report=quality_report,
            visual_storyboard=visual_storyboard,
            promo_bundle=promo_bundle,
            knowledge_transfer_kit=knowledge_kit,
            metadata={
                "persona": brief.persona,
                "topic": brief.topic,
                "timestamp": datetime.now().isoformat(),
            }
        )
