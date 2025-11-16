"""
Clarification handler for user interaction.

Manages the clarification loop when confidence is below threshold,
formulating questions and integrating user responses.
"""

from dataclasses import dataclass
from typing import List, Optional, Callable
from .confidence_scorer import ConfidenceScore
from ..config.orchestrator_config import ConfidenceConfig
from ..logging import get_logger, trace_context
from ..llm.model_manager import ModelManager


@dataclass
class ClarificationQuestion:
    """Represents a clarification question."""
    question: str
    priority: int  # 1 = highest priority
    category: str  # e.g., "missing_info", "ambiguity", "feasibility"


class ClarificationHandler:
    """
    Handles user clarification when confidence is insufficient.

    Formulates targeted questions based on confidence analysis
    and integrates user responses to improve understanding.
    """

    def __init__(
        self,
        config: ConfidenceConfig,
        model_manager: ModelManager,
        user_input_callback: Optional[Callable[[str], str]] = None
    ):
        """
        Initialize clarification handler.

        Args:
            config: Confidence configuration.
            model_manager: Model manager for AI calls.
            user_input_callback: Optional callback to get user input. If None, uses input().
        """
        self.config = config
        self.model_manager = model_manager
        self.user_input_callback = user_input_callback or self._default_input_callback
        self.logger = get_logger(__name__)

        self.clarification_history: List[str] = []

        self.logger.info("ClarificationHandler initialized", metadata={
            "max_rounds": config.max_clarification_rounds,
            "auto_clarify": config.auto_clarify,
        })

    def _default_input_callback(self, question: str) -> str:
        """Default callback that uses built-in input()."""
        print(f"\n🤔 {question}")
        return input("Your answer: ")

    def formulate_questions(
        self,
        confidence_score: ConfidenceScore,
        original_query: str
    ) -> List[ClarificationQuestion]:
        """
        Formulate clarification questions based on confidence analysis.

        Args:
            confidence_score: The confidence score indicating gaps.
            original_query: The original user query.

        Returns:
            List of clarification questions, ordered by priority.
        """
        with trace_context("formulate_clarifications") as span_id:
            self.logger.info("Formulating clarification questions", metadata={
                "overall_confidence": confidence_score.overall,
                "issues_count": len(confidence_score.issues),
                "suggested_clarifications": len(confidence_score.clarifications),
            })

            questions = []

            # Add questions from confidence analysis
            for i, clarification in enumerate(confidence_score.clarifications, start=1):
                questions.append(ClarificationQuestion(
                    question=clarification,
                    priority=i,
                    category="confidence_analysis"
                ))

            # Add AI-generated questions for low-scoring dimensions
            if confidence_score.clarity < 0.7:
                questions.extend(self._generate_clarity_questions(original_query))

            if confidence_score.completeness < 0.7:
                questions.extend(self._generate_completeness_questions(original_query))

            if confidence_score.feasibility < 0.7:
                questions.extend(self._generate_feasibility_questions(original_query))

            # Sort by priority and limit
            questions.sort(key=lambda q: q.priority)

            self.logger.info(f"Formulated {len(questions)} clarification questions")

            return questions[:5]  # Limit to 5 questions max

    def _generate_clarity_questions(self, query: str) -> List[ClarificationQuestion]:
        """Generate questions to improve clarity."""
        prompt = f"""The following user request lacks clarity. Generate 1-2 specific questions to clarify their intent.

Request: {query}

Provide questions as a simple numbered list."""

        try:
            response = self.model_manager.orchestrator_generate(prompt, temperature=0.5)
            questions = self._parse_questions(response.content, "clarity")
            return questions
        except Exception as e:
            self.logger.warning(f"Failed to generate clarity questions: {e}")
            return []

    def _generate_completeness_questions(self, query: str) -> List[ClarificationQuestion]:
        """Generate questions to gather missing information."""
        prompt = f"""The following user request is missing important details. Generate 1-2 specific questions to gather necessary information.

Request: {query}

Provide questions as a simple numbered list."""

        try:
            response = self.model_manager.orchestrator_generate(prompt, temperature=0.5)
            questions = self._parse_questions(response.content, "completeness")
            return questions
        except Exception as e:
            self.logger.warning(f"Failed to generate completeness questions: {e}")
            return []

    def _generate_feasibility_questions(self, query: str) -> List[ClarificationQuestion]:
        """Generate questions to assess feasibility."""
        prompt = f"""The following user request has unclear feasibility. Generate 1-2 specific questions to better understand constraints and expectations.

Request: {query}

Provide questions as a simple numbered list."""

        try:
            response = self.model_manager.orchestrator_generate(prompt, temperature=0.5)
            questions = self._parse_questions(response.content, "feasibility")
            return questions
        except Exception as e:
            self.logger.warning(f"Failed to generate feasibility questions: {e}")
            return []

    def _parse_questions(self, response: str, category: str) -> List[ClarificationQuestion]:
        """Parse AI response into ClarificationQuestion objects."""
        questions = []
        lines = response.strip().split('\n')

        for line in lines:
            line = line.strip()
            # Remove numbering (1., 2., etc.)
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                question_text = line.lstrip('0123456789.-•) ').strip()
                if question_text and len(question_text) > 10:
                    questions.append(ClarificationQuestion(
                        question=question_text,
                        priority=len(questions) + 1,
                        category=category
                    ))

        return questions

    def ask_clarifications(
        self,
        questions: List[ClarificationQuestion],
        original_query: str
    ) -> str:
        """
        Ask clarification questions and collect user responses.

        Args:
            questions: List of clarification questions.
            original_query: The original user query.

        Returns:
            Enhanced query incorporating user responses.
        """
        with trace_context("ask_clarifications") as span_id:
            self.logger.info(f"Asking {len(questions)} clarification questions")

            responses = []

            print("\n" + "="*60)
            print("I need some clarification to better understand your request.")
            print("="*60)

            for i, question in enumerate(questions, start=1):
                try:
                    answer = self.user_input_callback(f"Q{i}. {question.question}")

                    if answer and answer.strip():
                        responses.append({
                            'question': question.question,
                            'answer': answer.strip(),
                            'category': question.category,
                        })

                        self.clarification_history.append(
                            f"Q: {question.question}\nA: {answer.strip()}"
                        )

                        self.logger.info("Clarification received", metadata={
                            "question": question.question,
                            "answer_length": len(answer),
                            "category": question.category,
                        })

                except Exception as e:
                    self.logger.error(f"Error getting clarification: {e}", exc_info=True)

            # Synthesize enhanced query
            enhanced_query = self._synthesize_enhanced_query(
                original_query,
                responses
            )

            self.logger.info("Enhanced query created", metadata={
                "original_length": len(original_query),
                "enhanced_length": len(enhanced_query),
                "responses_count": len(responses),
            })

            return enhanced_query

    def _synthesize_enhanced_query(
        self,
        original_query: str,
        responses: List[dict]
    ) -> str:
        """
        Synthesize an enhanced query from original query and clarifications.

        Args:
            original_query: The original user query.
            responses: List of Q&A dictionaries.

        Returns:
            Enhanced, more complete query.
        """
        if not responses:
            return original_query

        # Build clarification context
        clarifications = "\n\n".join([
            f"Q: {r['question']}\nA: {r['answer']}"
            for r in responses
        ])

        prompt = f"""Given the original user request and their clarifying answers, synthesize an enhanced, complete request that incorporates all information.

**Original Request:**
{original_query}

**Clarifications:**
{clarifications}

**Your Task:**
Create a single, comprehensive request that includes all the information from both the original request and the clarifications. Keep it concise but complete.

Enhanced Request:"""

        try:
            response = self.model_manager.orchestrator_generate(
                prompt,
                temperature=0.3
            )

            enhanced = response.content.strip()

            # If the synthesis seems to have failed, fall back to concatenation
            if len(enhanced) < len(original_query) * 0.5:
                enhanced = f"{original_query}\n\nAdditional context:\n{clarifications}"

            return enhanced

        except Exception as e:
            self.logger.error("Failed to synthesize enhanced query", exc_info=True)
            # Fallback: concatenate original and clarifications
            return f"{original_query}\n\nAdditional context:\n{clarifications}"

    def get_clarification_context(self) -> str:
        """Get formatted clarification history for context."""
        if not self.clarification_history:
            return ""

        return "\n\n".join([
            f"Previous Clarification {i+1}:\n{clarif}"
            for i, clarif in enumerate(self.clarification_history)
        ])
