#!/usr/bin/env python3
"""
Quick test script to verify orchestrator implementation.

Tests basic functionality without requiring API keys.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        # Config imports
        from ai_agentic_workflow.config import (
            OrchestratorConfig,
            ModelConfig,
            ConfidenceConfig,
            ExecutionConfig,
            LoggingConfig,
            get_default_config,
        )
        print("✓ Config imports successful")

        # Logging imports
        from ai_agentic_workflow.logging import (
            StructuredLogger,
            get_logger,
            TraceManager,
            trace_context,
        )
        print("✓ Logging imports successful")

        # LLM imports
        from ai_agentic_workflow.llm import (
            ModelManager,
            ModelResponse,
            BaseProvider,
        )
        print("✓ LLM imports successful")

        # Orchestrator imports
        from ai_agentic_workflow.orchestrator import (
            Orchestrator,
            ConfidenceScorer,
            ClarificationHandler,
            TaskPlanner,
            TaskExecutor,
        )
        print("✓ Orchestrator imports successful")

        return True

    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """Test configuration validation."""
    print("\nTesting configuration validation...")

    try:
        from ai_agentic_workflow.config import get_default_config

        config = get_default_config()

        # Validate structure (API keys may be missing in test environment)
        errors = config.validate()

        # Filter out API key errors (expected in test environment)
        non_api_key_errors = [
            err for err in errors
            if "API key" not in err and "api_key" not in err
        ]

        if not non_api_key_errors:
            print("✓ Default config structure is valid (API keys not tested)")
        else:
            print("✗ Default config has structural errors:")
            for err in non_api_key_errors:
                print(f"  - {err}")
            return False

        # Test pre-configured profiles
        from ai_agentic_workflow.config import get_config_by_name

        profiles = ["default", "development", "local", "fast", "accurate"]
        for profile in profiles:
            try:
                cfg = get_config_by_name(profile)
                errors = cfg.validate()
                non_api_key_errors = [
                    err for err in errors
                    if "API key" not in err and "api_key" not in err
                ]

                if not non_api_key_errors:
                    print(f"✓ Profile '{profile}' structure is valid")
                else:
                    print(f"✗ Profile '{profile}' has structural errors")
                    return False
            except Exception as e:
                print(f"✗ Failed to load profile '{profile}': {e}")
                return False

        return True

    except Exception as e:
        print(f"✗ Config validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logging_system():
    """Test logging and tracing."""
    print("\nTesting logging system...")

    try:
        from ai_agentic_workflow.logging import (
            get_logger,
            trace_context,
            get_trace_manager,
        )

        # Test logger
        logger = get_logger(__name__)
        logger.info("Test log message")
        print("✓ Logger created successfully")

        # Test trace manager
        trace_manager = get_trace_manager()
        trace_id = trace_manager.start_trace(metadata={"test": "data"})
        print(f"✓ Trace started: {trace_id}")

        # Test span
        with trace_context("test_span", trace_id=trace_id):
            logger.info("Inside trace span")

        trace_manager.end_trace(trace_id)
        print("✓ Trace completed")

        # Export trace
        trace_json = trace_manager.export_trace(trace_id)
        if trace_json:
            print("✓ Trace exported successfully")
        else:
            print("⚠ Trace export returned None")

        return True

    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_task_structures():
    """Test task planning structures."""
    print("\nTesting task structures...")

    try:
        from ai_agentic_workflow.orchestrator import Task, TaskStatus, TaskSource

        # Create a test task
        task = Task(
            task_id="T1",
            title="Test Task",
            description="This is a test task",
            source=TaskSource.LLM_GENERATION,
            source_details={"prompt": "test"},
            success_criteria=["Complete successfully"],
            priority=1,
        )

        print(f"✓ Task created: {task.task_id}")

        # Test task methods
        assert task.is_ready([]), "Task should be ready with no dependencies"
        print("✓ Task dependency check works")

        # Test serialization
        task_dict = task.to_dict()
        assert isinstance(task_dict, dict), "Task serialization failed"
        print("✓ Task serialization works")

        return True

    except Exception as e:
        print(f"✗ Task structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*70)
    print("ORCHESTRATOR IMPLEMENTATION TEST SUITE")
    print("="*70)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Config Validation", test_config_validation()))
    results.append(("Logging System", test_logging_system()))
    results.append(("Task Structures", test_task_structures()))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("="*70)

    if all_passed:
        print("\n🎉 All tests passed!")
        print("\nNext steps:")
        print("1. Set up your API keys in .env file")
        print("2. Run: python examples/basic_orchestrator_example.py")
        print("3. See ORCHESTRATOR_README.md for full documentation")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
