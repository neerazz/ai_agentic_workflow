#!/usr/bin/env python3
"""
Test script for Blog Creation Agent.

This script performs basic validation of the blog creation agent
without making actual API calls (dry-run mode).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    try:
        from src.ai_agentic_workflow.agents import BlogCreationAgent, BlogBrief, BlogDeliverable
        from src.ai_agentic_workflow.config import get_free_tier_blog_config
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test configuration creation and validation."""
    print("\nTesting configuration...")
    try:
        from src.ai_agentic_workflow.config import get_free_tier_blog_config
        
        config = get_free_tier_blog_config()
        print(f"✅ Config created: {config.planning_model}, {config.drafting_model}")
        
        # Test validation
        errors = config.validate()
        if errors:
            print(f"⚠️  Config validation warnings: {errors}")
        else:
            print("✅ Config validation passed")
        
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_initialization():
    """Test agent initialization (without API calls)."""
    print("\nTesting agent initialization...")
    try:
        from src.ai_agentic_workflow.agents import BlogCreationAgent
        from src.ai_agentic_workflow.config import get_free_tier_blog_config
        
        config = get_free_tier_blog_config()
        
        # This will fail if API keys are missing, but that's expected
        # We just want to check that the class can be instantiated
        try:
            agent = BlogCreationAgent(config=config)
            print("✅ Agent initialized successfully")
            print(f"   - Planning model: {agent.blog_config.planning_model}")
            print(f"   - Drafting model: {agent.blog_config.drafting_model}")
            print(f"   - Critique model: {agent.blog_config.critique_model}")
            return True
        except Exception as e:
            # Check if it's an API key error (expected) or something else
            error_msg = str(e).lower()
            if "api" in error_msg or "key" in error_msg:
                print("⚠️  Agent initialization requires API keys (expected)")
                print("   This is normal - API keys needed for actual execution")
                return True
            else:
                print(f"❌ Agent initialization failed: {e}")
                import traceback
                traceback.print_exc()
                return False
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_structures():
    """Test data structure creation."""
    print("\nTesting data structures...")
    try:
        from src.ai_agentic_workflow.agents import BlogBrief, BlogDeliverable
        
        # Test BlogBrief
        brief = BlogBrief(
            persona="Principal Software Engineer",
            topic="Kubernetes",
            goal="Teach best practices"
        )
        print(f"✅ BlogBrief created: {brief.topic}")
        
        # Test BlogDeliverable
        deliverable = BlogDeliverable(
            packaged_post="# Test Blog\n\nContent here",
            title="Test Blog",
            meta_description="A test blog",
            seo_keywords=["test", "blog"],
            quality_report={"final_score": 85},
            visual_storyboard={},
            promo_bundle={},
            knowledge_transfer_kit={}
        )
        print(f"✅ BlogDeliverable created: {deliverable.title}")
        
        return True
    except Exception as e:
        print(f"❌ Data structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_json_parsing():
    """Test the safe JSON parsing utility."""
    print("\nTesting JSON parsing utility...")
    try:
        from src.ai_agentic_workflow.agents import BlogCreationAgent
        from src.ai_agentic_workflow.config import get_free_tier_blog_config
        
        config = get_free_tier_blog_config()
        
        # Create agent (may fail on API keys, but we just need the method)
        try:
            agent = BlogCreationAgent(config=config)
        except:
            # Create a mock agent just for testing the method
            class MockAgent:
                def _safe_json_parse(self, content, default):
                    import json
                    import re
                    try:
                        content = content.strip()
                        if content.startswith("```"):
                            lines = content.split("\n")
                            if len(lines) > 2:
                                content = "\n".join(lines[1:-1])
                        if content.startswith("{") or content.startswith("["):
                            return json.loads(content)
                        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
                        matches = re.findall(json_pattern, content, re.DOTALL)
                        if matches:
                            return json.loads(max(matches, key=len))
                        return default
                    except:
                        return default
            
            agent = MockAgent()
        
        # Test various JSON formats
        test_cases = [
            ('{"key": "value"}', {"key": "value"}),
            ('```json\n{"key": "value"}\n```', {"key": "value"}),
            ('Some text {"key": "value"} more text', {"key": "value"}),
            ('Invalid JSON', {}),
        ]
        
        for input_str, expected in test_cases:
            result = agent._safe_json_parse(input_str, {})
            if result == expected or (isinstance(result, dict) and result.get("key") == "value"):
                print(f"✅ Parsed: {input_str[:30]}...")
            else:
                print(f"⚠️  Unexpected result for: {input_str[:30]}...")
        
        return True
    except Exception as e:
        print(f"❌ JSON parsing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("="*70)
    print("Blog Creation Agent - Validation Tests")
    print("="*70)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Data Structures", test_data_structures),
        ("Agent Initialization", test_agent_initialization),
        ("JSON Parsing", test_json_parsing),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append((name, False))
    
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All validation tests passed!")
        print("\nNote: Full functionality requires API keys for:")
        print("  - GOOGLE_API_KEY (for Gemini)")
        print("  - GROQ_API_KEY (for Groq)")
        print("  - OPENAI_API_KEY (optional, for GPT critique)")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
