#!/usr/bin/env python3
"""
LM Studio Local Model Example

Demonstrates using the orchestrator with local models via LM Studio.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_agentic_workflow.orchestrator import Orchestrator
from ai_agentic_workflow.config import get_local_lmstudio_config
from ai_agentic_workflow.logging import setup_logging


def main():
    """Run LM Studio orchestrator example."""

    # Setup logging
    setup_logging(level="INFO", structured=False)

    print("="*70)
    print("LM STUDIO LOCAL MODEL EXAMPLE")
    print("="*70)
    print()
    print("NOTE: Ensure LM Studio is running on http://localhost:1234")
    print("      and you have a model loaded.")
    print()

    # Create orchestrator with LM Studio config
    config = get_local_lmstudio_config()

    # You can customize the config further
    config.model.lmstudio_base_url = "http://localhost:1234/v1"
    config.model.lmstudio_model = "local-model"  # Or your specific model name

    orchestrator = Orchestrator(config)

    # Example query
    user_query = """
    Explain the concept of recursion in programming and provide a simple example
    in Python.
    """

    print("Processing query with local model...")
    print(f"Query: {user_query.strip()}")
    print()

    # Process the query
    result = orchestrator.process(user_query)

    # Print summary
    result.print_summary()

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
