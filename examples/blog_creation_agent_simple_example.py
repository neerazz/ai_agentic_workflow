#!/usr/bin/env python3
"""
Simple example of using the Blog Creation Agent.

This demonstrates the basic usage with minimal code.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_agentic_workflow.agents import BlogCreationAgent
from src.ai_agentic_workflow.config import get_free_tier_blog_config


def main():
    """Simple example of blog creation."""
    
    print("🚀 Initializing Blog Creation Agent...")
    
    # Initialize agent with free-tier config (Gemini + Groq)
    config = get_free_tier_blog_config()
    agent = BlogCreationAgent(config=config)
    
    # Option 1: Simple topic input
    print("\n📝 Creating blog with simple topic...")
    user_input = "Write a blog about Kubernetes best practices for production deployments"
    
    result = agent.execute(user_input)
    
    if result.success:
        deliverable = result.output
        
        print(f"\n✅ Blog created successfully!")
        print(f"📊 Title: {deliverable.title}")
        print(f"📈 Quality Score: {deliverable.quality_report.get('final_score', 'N/A')}/100")
        print(f"\n📄 Blog Preview (first 500 chars):")
        print("-" * 70)
        print(deliverable.packaged_post[:500] + "...")
        print("-" * 70)
        
        # Option 2: Structured input using BlogBrief
        print("\n\n" + "="*70)
        print("Example 2: Using structured BlogBrief")
        print("="*70)
        
        from src.ai_agentic_workflow.agents import BlogBrief
        
        brief = BlogBrief(
            persona="Principal Software Engineer",
            topic="Microservices architecture patterns",
            goal="Teach best practices for building scalable microservices",
            voice="Pragmatic mentor, data-backed, grounded optimism",
            target_audience=["junior", "mid", "senior"],
            brand_pillars=["Craftsmanship", "Clarity", "Community"]
        )
        
        result2 = agent.execute(
            user_input="",  # Empty since we're using structured brief
            context={"brief": brief}
        )
        
        if result2.success:
            deliverable2 = result2.output
            print(f"\n✅ Second blog created!")
            print(f"📊 Title: {deliverable2.title}")
            print(f"📈 Quality Score: {deliverable2.quality_report.get('final_score', 'N/A')}/100")
    else:
        print(f"\n❌ Blog creation failed: {result.error}")


if __name__ == "__main__":
    main()
