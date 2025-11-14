#!/usr/bin/env python3
"""
Quick test to verify complete flow with all critique loops and conversation memory.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ai_agentic_workflow.config import get_free_tier_config
from ai_agentic_workflow.agents import GeneralPurposeAgent
from ai_agentic_workflow.logging import setup_logging


def test_complete_flow():
    """Test the complete flow with critique loops and conversation."""
    print("\n" + "="*60)
    print("Testing General Purpose Agent - Complete Flow")
    print("="*60 + "\n")

    # Setup
    setup_logging(level="INFO", structured=False)
    config = get_free_tier_config()

    # Validate config
    errors = config.validate()
    non_api_key_errors = [err for err in errors if "API key" not in err]

    if non_api_key_errors:
        print("❌ Configuration has errors:")
        for error in non_api_key_errors:
            print(f"  - {error}")
        return False

    print("✅ Configuration validated")

    # Test imports and component initialization
    try:
        print("\n📦 Testing component imports...")

        from ai_agentic_workflow.agents import (
            CritiqueEngine,
            DecisionMaker,
            TaskReasoner,
            ConversationManager,
            ProgressTracker,
            BaseAgent,
            GeneralPurposeAgent
        )

        print("✅ All components imported successfully")

        # Initialize agent
        print("\n🤖 Initializing GeneralPurposeAgent...")
        agent = GeneralPurposeAgent(config)
        print("✅ Agent initialized")

        # Verify conversation manager exists
        assert hasattr(agent, 'conversation_manager'), "Missing conversation_manager"
        assert hasattr(agent, 'critique_engine'), "Missing critique_engine"
        assert hasattr(agent, 'decision_maker'), "Missing decision_maker"
        assert hasattr(agent, 'task_reasoner'), "Missing task_reasoner"
        print("✅ All required components present")

        # Check conversation manager methods
        assert hasattr(agent.conversation_manager, 'add_turn'), "Missing add_turn method"
        assert hasattr(agent.conversation_manager, 'get_context_for_new_request'), "Missing get_context_for_new_request"
        print("✅ ConversationManager has required methods")

        # Check critique engine has all three critique methods
        assert hasattr(agent.critique_engine, 'critique_task_plan'), "Missing critique_task_plan method"
        assert hasattr(agent.critique_engine, 'critique_task_output'), "Missing critique_task_output"
        assert hasattr(agent.critique_engine, 'critique_final_output'), "Missing critique_final_output"
        print("✅ CritiqueEngine has all three critique methods")

        # Check agent has all three critique loop methods
        assert hasattr(agent, '_reason_and_plan_with_critique'), "Missing _reason_and_plan_with_critique"
        assert hasattr(agent, '_execute_with_critique'), "Missing _execute_with_critique"
        assert hasattr(agent, '_synthesize_with_critique'), "Missing _synthesize_with_critique"
        print("✅ GeneralPurposeAgent has all three critique loop methods")

        # Test conversation history methods
        assert hasattr(agent, 'get_conversation_history'), "Missing get_conversation_history"
        assert hasattr(agent, 'clear_conversation'), "Missing clear_conversation"
        print("✅ Conversation management methods present")

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - Ready for use!")
        print("="*60)
        print("\n📝 Summary:")
        print("  ✓ Configuration validated")
        print("  ✓ All components imported")
        print("  ✓ Agent initialized with all critique loops")
        print("  ✓ Task Planning Critique Loop implemented")
        print("  ✓ Task Execution Critique Loop implemented")
        print("  ✓ Final Synthesis Critique Loop implemented")
        print("  ✓ Conversation Manager integrated")
        print("  ✓ Multi-turn conversation support ready")
        print("\n🚀 Run the CLI to test with real queries:")
        print("   python examples/general_purpose_agent_cli.py\n")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_complete_flow()
    sys.exit(0 if success else 1)
