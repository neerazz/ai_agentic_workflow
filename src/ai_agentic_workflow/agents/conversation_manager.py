"""
Conversation Manager for chat session state management.

Tracks user Q&A history without internal reasoning details to keep
token counts manageable while maintaining conversation context.
"""

import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..logging import get_logger


@dataclass
class ConversationTurn:
    """Single turn in a conversation."""
    turn_id: int
    user_query: str
    ai_response: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'turn_id': self.turn_id,
            'user_query': self.user_query,
            'ai_response': self.ai_response,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
        }


class ConversationManager:
    """
    Manages conversation state across multiple turns.

    Stores ONLY user queries and AI responses (not internal reasoning).
    Provides smart context passing to balance completeness vs token usage.
    """

    def __init__(
        self,
        max_history_turns: int = 10,
        max_context_tokens: int = 4000
    ):
        """
        Initialize conversation manager.

        Args:
            max_history_turns: Maximum conversation turns to keep.
            max_context_tokens: Approximate max tokens for context.
        """
        self.turns: List[ConversationTurn] = []
        self.max_history_turns = max_history_turns
        self.max_context_tokens = max_context_tokens
        self.logger = get_logger(__name__)

        self.logger.info("ConversationManager initialized", metadata={
            "max_turns": max_history_turns,
            "max_context_tokens": max_context_tokens,
        })

    def add_turn(
        self,
        user_query: str,
        ai_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a conversation turn.

        Args:
            user_query: User's question/request.
            ai_response: AI's final response (NOT reasoning/tasks).
            metadata: Optional metadata (quality score, execution time, etc.).
        """
        turn = ConversationTurn(
            turn_id=len(self.turns) + 1,
            user_query=user_query,
            ai_response=ai_response,
            metadata=metadata or {}
        )

        self.turns.append(turn)

        # Trim history if exceeds max
        if len(self.turns) > self.max_history_turns:
            removed = self.turns.pop(0)
            self.logger.info(f"Removed old turn {removed.turn_id} (max history reached)")

        self.logger.info(f"Added turn {turn.turn_id} to conversation")

    def get_context_for_new_request(
        self,
        current_request: str,
        include_last_n: Optional[int] = None
    ) -> str:
        """
        Get conversation context for a new request.

        Returns formatted context with user Q&A history ONLY
        (no internal reasoning, tasks, critiques).

        Args:
            current_request: The new user request.
            include_last_n: Number of recent turns to include (None = smart selection).

        Returns:
            Formatted context string.
        """
        if not self.turns:
            return ""

        # Determine how many turns to include
        if include_last_n is None:
            # Smart selection based on token estimate
            include_last_n = self._smart_select_turns(current_request)
        else:
            include_last_n = min(include_last_n, len(self.turns))

        # Get recent turns
        recent_turns = self.turns[-include_last_n:] if include_last_n > 0 else []

        if not recent_turns:
            return ""

        # Format context
        context_parts = ["**Conversation History:**\n"]

        for turn in recent_turns:
            context_parts.append(f"**Turn {turn.turn_id}:**")
            context_parts.append(f"User: {turn.user_query}")
            context_parts.append(f"AI: {turn.ai_response[:500]}...")  # Truncate long responses
            context_parts.append("")  # Blank line

        context = "\n".join(context_parts)

        self.logger.info(f"Generated context from last {len(recent_turns)} turns")

        return context

    def _smart_select_turns(self, current_request: str) -> int:
        """
        Smart selection of how many turns to include.

        Uses heuristics to balance context vs tokens:
        - If request mentions "previous", "earlier", "before" → include more turns
        - If request is standalone → include fewer turns
        - Estimate token count and stay under limit
        """
        # Keywords suggesting need for more context
        context_keywords = [
            'previous', 'earlier', 'before', 'above', 'mentioned',
            'said', 'told', 'discussed', 'talked', 'asked'
        ]

        needs_more_context = any(
            keyword in current_request.lower()
            for keyword in context_keywords
        )

        if needs_more_context:
            # Include more turns (up to 5)
            target_turns = min(5, len(self.turns))
        else:
            # Include fewer turns (up to 3)
            target_turns = min(3, len(self.turns))

        # Estimate tokens and adjust if needed
        estimated_tokens = self._estimate_context_tokens(target_turns)

        while estimated_tokens > self.max_context_tokens and target_turns > 1:
            target_turns -= 1
            estimated_tokens = self._estimate_context_tokens(target_turns)

        self.logger.debug(f"Smart select: {target_turns} turns (estimated {estimated_tokens} tokens)")

        return target_turns

    def _estimate_context_tokens(self, num_turns: int) -> int:
        """
        Estimate token count for context.

        Rough estimate: 1 token ≈ 4 characters.
        """
        if num_turns == 0 or not self.turns:
            return 0

        recent_turns = self.turns[-num_turns:]

        total_chars = sum(
            len(turn.user_query) + len(turn.ai_response[:500])
            for turn in recent_turns
        )

        # Add overhead for formatting
        total_chars += num_turns * 50

        # Rough token estimate
        estimated_tokens = total_chars // 4

        return estimated_tokens

    def get_full_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history as list of dicts."""
        return [turn.to_dict() for turn in self.turns]

    def clear_history(self):
        """Clear all conversation history."""
        self.turns.clear()
        self.logger.info("Conversation history cleared")

    def export_to_json(self) -> str:
        """Export conversation to JSON."""
        return json.dumps(self.get_full_history(), indent=2)

    def get_last_turn(self) -> Optional[ConversationTurn]:
        """Get the most recent turn."""
        return self.turns[-1] if self.turns else None

    def get_turn_by_id(self, turn_id: int) -> Optional[ConversationTurn]:
        """Get a specific turn by ID."""
        for turn in self.turns:
            if turn.turn_id == turn_id:
                return turn
        return None

    def get_summary(self) -> str:
        """Get a summary of the conversation."""
        if not self.turns:
            return "No conversation history"

        return f"Conversation with {len(self.turns)} turns (from {self.turns[0].timestamp} to {self.turns[-1].timestamp})"
