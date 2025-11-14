#!/usr/bin/env python3
"""
Advanced Orchestrator Example

Demonstrates advanced usage with custom configuration, multiple
providers, and detailed result analysis.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_agentic_workflow.orchestrator import Orchestrator
from ai_agentic_workflow.config import (
    OrchestratorConfig,
    ModelConfig,
    ConfidenceConfig,
    ExecutionConfig,
    LoggingConfig,
    ModelProvider,
    ExecutionStrategy,
)
from ai_agentic_workflow.logging import setup_logging


def create_custom_config() -> OrchestratorConfig:
    """Create a custom configuration."""

    return OrchestratorConfig(
        model=ModelConfig(
            # Use different models for different stages
            orchestrator_provider=ModelProvider.ANTHROPIC,
            orchestrator_model="claude-3-5-sonnet-20241022",
            orchestrator_temperature=0.7,

            planner_provider=ModelProvider.OPENAI,
            planner_model="gpt-4o",
            planner_temperature=0.3,

            executor_provider=ModelProvider.ANTHROPIC,
            executor_model="claude-3-5-sonnet-20241022",
            executor_temperature=0.5,
        ),
        confidence=ConfidenceConfig(
            min_confidence_threshold=0.80,  # Higher threshold for accuracy
            max_clarification_rounds=3,
            auto_clarify=True,
            # Custom weights
            clarity_weight=0.35,
            completeness_weight=0.35,
            feasibility_weight=0.20,
            specificity_weight=0.10,
        ),
        execution=ExecutionConfig(
            strategy=ExecutionStrategy.GREEDY,
            max_retries=3,
            retry_backoff=2.0,
            validate_results=True,
            fail_fast=False,  # Continue on errors to see all failures
        ),
        logging=LoggingConfig(
            log_level="DEBUG",
            structured_logging=True,
            enable_tracing=True,
            log_model_calls=True,
            export_traces=True,
            trace_export_path="./traces",
        ),
    )


def main():
    """Run advanced orchestrator example."""

    # Setup logging with structured output
    setup_logging(level="DEBUG", structured=True)

    print("="*70)
    print("ADVANCED ORCHESTRATOR EXAMPLE")
    print("="*70)
    print()

    # Create orchestrator with custom config
    config = create_custom_config()

    # Validate configuration
    print("Configuration Validation:")
    print(config.get_validation_report())
    print()

    orchestrator = Orchestrator(config)

    # Complex query that will benefit from clarification
    user_query = """
    I want to build something that analyzes data and provides insights.
    """

    print("Processing complex query (may require clarification)...")
    print(f"Query: {user_query.strip()}")
    print()

    # Process the query
    result = orchestrator.process(user_query)

    # Print detailed summary
    result.print_summary()

    # Analyze results in detail
    print("\n" + "="*70)
    print("DETAILED ANALYSIS")
    print("="*70)

    if result.confidence_score:
        print("\nConfidence Analysis:")
        if result.confidence_score.issues:
            print("  Issues identified:")
            for issue in result.confidence_score.issues:
                print(f"    - {issue}")

        if result.confidence_score.clarifications:
            print("  Suggested clarifications:")
            for clarif in result.confidence_score.clarifications:
                print(f"    - {clarif}")

    if result.task_plan and result.task_plan.warnings:
        print("\nTask Plan Warnings:")
        for warning in result.task_plan.warnings:
            print(f"  - {warning}")

    if result.execution_results:
        print("\nTask Execution Details:")
        for task_id, exec_result in result.execution_results.items():
            status = "✓" if exec_result.success else "✗"
            print(f"  {status} {task_id}: {exec_result.execution_time:.2f}s")
            if exec_result.error:
                print(f"      Error: {exec_result.error}")
            if exec_result.retries > 0:
                print(f"      Retries: {exec_result.retries}")

    # Save detailed results
    with open("advanced_orchestrator_result.json", "w") as f:
        f.write(result.to_json())

    print("\nDetailed results saved to: advanced_orchestrator_result.json")

    # Export trace if available
    if result.trace_id:
        from ai_agentic_workflow.logging import get_trace_manager
        trace_manager = get_trace_manager()
        trace_json = trace_manager.export_trace(result.trace_id)

        if trace_json:
            with open("advanced_orchestrator_trace.json", "w") as f:
                f.write(trace_json)
            print(f"Trace exported to: advanced_orchestrator_trace.json")

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
