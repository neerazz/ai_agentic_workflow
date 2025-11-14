#!/usr/bin/env python3
"""
Test Gradio UI imports and basic functionality
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    print("\n" + "="*60)
    print("Testing Gradio UI Dependencies")
    print("="*60 + "\n")

    # Test gradio import
    print("📦 Testing Gradio import...")
    import gradio as gr
    print(f"✅ Gradio version: {gr.__version__}")

    # Test other imports
    print("\n📦 Testing agent imports...")
    from ai_agentic_workflow.agents import GeneralPurposeAgent
    from ai_agentic_workflow.config import get_free_tier_config
    print("✅ Agent imports successful")

    # Test basic UI creation (without launching)
    print("\n🎨 Testing UI creation...")

    def dummy_function():
        return "Test"

    with gr.Blocks() as demo:
        gr.Markdown("# Test")
        btn = gr.Button("Test")
        output = gr.Textbox()
        btn.click(dummy_function, outputs=output)

    print("✅ UI creation successful")

    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60)
    print("\nYou can now run:")
    print("  python examples/general_purpose_agent_gradio.py\n")

except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nPlease install missing dependencies:")
    print("  pip install gradio")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
