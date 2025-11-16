"""
Confidence scoring system for user query understanding.

Evaluates multiple dimensions of query comprehension to determine
if the orchestrator has sufficient understanding to proceed.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from ..config.orchestrator_config import ConfidenceConfig
from ..logging import get_logger, trace_context
from ..llm.model_manager import ModelManager


@dataclass
class ConfidenceScore:
    """
    Multi-dimensional confidence score for query understanding.
    """
    # Individual dimension scores (0.0 - 1.0)
    clarity: float  # How clear and unambiguous is the request?
    completeness: float  # Are all necessary details provided?
    feasibility: float  # Can this request be reasonably fulfilled?
    specificity: float  # How specific vs. vague is the request?

    # Overall confidence score (weighted average)
    overall: float

    # Identified issues or gaps
    issues: List[str]

    # Suggested clarifications
    clarifications: List[str]

    def __post_init__(self):
        """Validate scores are in valid range."""
        for field_name in ['clarity', 'completeness', 'feasibility', 'specificity', 'overall']:
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} score must be between 0.0 and 1.0, got {value}")

    def is_confident(self, threshold: float) -> bool:
        """Check if overall confidence meets threshold."""
        return self.overall >= threshold

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'clarity': self.clarity,
            'completeness': self.completeness,
            'feasibility': self.feasibility,
            'specificity': self.specificity,
            'overall': self.overall,
            'is_confident': self.overall >= 0.75,
            'issues': self.issues,
            'clarifications': self.clarifications,
        }

    def __repr__(self) -> str:
        return (
            f"ConfidenceScore(overall={self.overall:.2f}, "
            f"clarity={self.clarity:.2f}, completeness={self.completeness:.2f}, "
            f"feasibility={self.feasibility:.2f}, specificity={self.specificity:.2f})"
        )


class ConfidenceScorer:
    """
    Evaluates confidence in understanding user queries.

    Uses AI-powered analysis to assess multiple dimensions of
    query comprehension and identify areas needing clarification.
    """

    def __init__(self, config: ConfidenceConfig, model_manager: ModelManager):
        """
        Initialize confidence scorer.

        Args:
            config: Confidence configuration.
            model_manager: Model manager for AI calls.
        """
        self.config = config
        self.model_manager = model_manager
        self.logger = get_logger(__name__)

        self.logger.info("ConfidenceScorer initialized", metadata={
            "threshold": config.min_confidence_threshold,
            "weights": {
                "clarity": config.clarity_weight,
                "completeness": config.completeness_weight,
                "feasibility": config.feasibility_weight,
                "specificity": config.specificity_weight,
            }
        })

    def score(self, user_query: str, context: Optional[str] = None) -> ConfidenceScore:
        """
        Evaluate confidence in understanding a user query.

        Args:
            user_query: The user's request or question.
            context: Optional additional context or conversation history.

        Returns:
            ConfidenceScore with multi-dimensional analysis.
        """
        with trace_context("confidence_scoring") as span_id:
            self.logger.info("Scoring query confidence", metadata={
                "query_length": len(user_query),
                "has_context": context is not None,
            })

            # Build evaluation prompt
            prompt = self._build_evaluation_prompt(user_query, context)

            # Get AI analysis
            try:
                response = self.model_manager.orchestrator_generate(
                    prompt=prompt,
                    temperature=0.3,  # Lower temperature for more consistent scoring
                )

                # Parse response
                score = self._parse_response(response.content)

                self.logger.info("Confidence score calculated", metadata={
                    "overall": score.overall,
                    "clarity": score.clarity,
                    "completeness": score.completeness,
                    "feasibility": score.feasibility,
                    "specificity": score.specificity,
                    "issues_count": len(score.issues),
                    "clarifications_count": len(score.clarifications),
                })

                return score

            except Exception as e:
                self.logger.error("Confidence scoring failed", metadata={
                    "error": str(e),
                }, exc_info=True)

                # Return conservative score on error
                return ConfidenceScore(
                    clarity=0.5,
                    completeness=0.5,
                    feasibility=0.5,
                    specificity=0.5,
                    overall=0.5,
                    issues=["Failed to analyze query confidence"],
                    clarifications=["Please rephrase your request for better understanding"],
                )

    def _build_evaluation_prompt(self, user_query: str, context: Optional[str]) -> str:
        """Build the prompt for confidence evaluation."""
        prompt = f"""You are an expert at analyzing user requests to determine if you have sufficient information to help them effectively.

**User Query:**
{user_query}
"""

        if context:
            prompt += f"""
**Additional Context:**
{context}
"""

        prompt += """
**Your Task:**
Analyze this request across four dimensions and provide scores from 0.0 to 1.0:

1. **Clarity** (0.0 - 1.0): How clear and unambiguous is the request?
   - 1.0 = Perfectly clear, no ambiguity
   - 0.5 = Some ambiguity but general intent is clear
   - 0.0 = Very unclear or contradictory

2. **Completeness** (0.0 - 1.0): Are all necessary details provided?
   - 1.0 = All required information is present
   - 0.5 = Some key details are missing
   - 0.0 = Critical information is missing

3. **Feasibility** (0.0 - 1.0): Can this request be reasonably fulfilled?
   - 1.0 = Clearly achievable and realistic
   - 0.5 = Possible but challenging or unclear how
   - 0.0 = Not feasible or impossible

4. **Specificity** (0.0 - 1.0): How specific vs. vague is the request?
   - 1.0 = Very specific with concrete details
   - 0.5 = Somewhat specific but could be more detailed
   - 0.0 = Very vague or general

Also identify:
- **Issues**: Any problems, ambiguities, or concerns with the request
- **Clarifications**: Specific questions that would improve understanding

**Response Format (JSON):**
```json
{
    "clarity": 0.0-1.0,
    "completeness": 0.0-1.0,
    "feasibility": 0.0-1.0,
    "specificity": 0.0-1.0,
    "issues": ["list", "of", "identified", "issues"],
    "clarifications": ["list", "of", "suggested", "questions"]
}
```

Respond ONLY with the JSON object, no additional text.
"""

        return prompt

    def _parse_response(self, response_text: str) -> ConfidenceScore:
        """
        Parse AI response into ConfidenceScore.

        Args:
            response_text: Raw response from AI model.

        Returns:
            ConfidenceScore object.
        """
        try:
            # Extract JSON from response (may be wrapped in markdown code blocks)
            json_text = response_text.strip()

            # Remove markdown code blocks if present
            if json_text.startswith("```"):
                lines = json_text.split("\n")
                json_text = "\n".join(lines[1:-1]) if len(lines) > 2 else json_text

            # Parse JSON
            data = json.loads(json_text)

            # Extract scores
            clarity = float(data.get('clarity', 0.5))
            completeness = float(data.get('completeness', 0.5))
            feasibility = float(data.get('feasibility', 0.5))
            specificity = float(data.get('specificity', 0.5))

            # Calculate weighted overall score
            overall = (
                clarity * self.config.clarity_weight +
                completeness * self.config.completeness_weight +
                feasibility * self.config.feasibility_weight +
                specificity * self.config.specificity_weight
            )

            # Extract issues and clarifications
            issues = data.get('issues', [])
            clarifications = data.get('clarifications', [])

            return ConfidenceScore(
                clarity=clarity,
                completeness=completeness,
                feasibility=feasibility,
                specificity=specificity,
                overall=overall,
                issues=issues,
                clarifications=clarifications,
            )

        except Exception as e:
            self.logger.error("Failed to parse confidence response", metadata={
                "error": str(e),
                "response": response_text[:500],
            }, exc_info=True)

            # Return conservative score
            return ConfidenceScore(
                clarity=0.5,
                completeness=0.5,
                feasibility=0.5,
                specificity=0.5,
                overall=0.5,
                issues=["Failed to parse confidence analysis"],
                clarifications=["Please provide more details about your request"],
            )
