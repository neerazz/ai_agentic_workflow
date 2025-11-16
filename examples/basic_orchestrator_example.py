#!/usr/bin/env python3
"""
Basic Orchestrator Example

Demonstrates simple usage of the agentic workflow orchestrator
with default configuration.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_agentic_workflow.orchestrator import Orchestrator
from ai_agentic_workflow.config import get_default_config
from ai_agentic_workflow.logging import setup_logging


def main():
    """Run basic orchestrator example."""

    # Setup logging
    setup_logging(level="INFO", structured=False)

    print("="*70)
    print("BASIC ORCHESTRATOR EXAMPLE")
    print("="*70)
    print()

    # Create orchestrator with default config
    config = get_default_config()
    orchestrator = Orchestrator(config)

    # Example query
    user_query = """
    I need to analyze the sentiment of customer reviews for my product.
    Can you help me understand how to approach this and what steps are involved?
    """

    print("Processing query...")
    print(f"Query: {user_query.strip()}")
    print()

    # Process the query
    result = orchestrator.process(user_query)

    # Print summary
    result.print_summary()

    # Optionally save detailed results to file
    with open("orchestrator_result.json", "w") as f:
        f.write(result.to_json())

    print("Detailed results saved to: orchestrator_result.json")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
