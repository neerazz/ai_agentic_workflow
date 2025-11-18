#!/usr/bin/env python3
"""
Example: Blog Creation with LinkedIn Persona Extraction

Demonstrates how to use the Blog Creation Agent with LinkedIn posts
and profile data for efficient persona extraction and reuse.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_agentic_workflow.agents import BlogCreationAgent, PersonaExtractor, PersonaMemory
from src.ai_agentic_workflow.config import get_free_tier_blog_config


# Example LinkedIn data (replace with your actual data)
EXAMPLE_LINKEDIN_POSTS = [
    """
    Just shipped a major refactor of our microservices architecture. 
    The key was breaking down the monolith into smaller, focused services.
    Here's what I learned: always start with the data model, not the API.
    #Microservices #SoftwareArchitecture
    """,
    """
    Spent the weekend debugging a Kubernetes deployment issue. 
    Turns out it was a resource limit problem that only showed up under load.
    Lesson: always test with production-like traffic patterns.
    #Kubernetes #DevOps
    """,
    """
    Mentoring junior developers has been one of the most rewarding parts 
    of my career. The key is to ask questions, not give answers.
    #Mentorship #SoftwareEngineering
    """,
]

EXAMPLE_LINKEDIN_PROFILE = """
John Doe
Principal Software Engineer at TechCorp

Experience:
- Principal Software Engineer, TechCorp (2020-Present)
  - Led microservices migration for 50+ services
  - Built Kubernetes-based deployment platform
  - Mentored team of 10 engineers

- Senior Software Engineer, StartupXYZ (2018-2020)
  - Designed and implemented distributed systems
  - Reduced deployment time by 60%

Skills: Python, Kubernetes, Microservices, Docker, AWS, System Design
"""


def main():
    """Demonstrate persona extraction and blog creation."""
    
    print("="*70)
    print("Blog Creation with Persona Extraction")
    print("="*70)
    
    # Initialize agent
    print("\n1. Initializing Blog Creation Agent...")
    config = get_free_tier_blog_config()
    agent = BlogCreationAgent(config=config)
    
    # Option 1: Extract persona first, then create blog
    print("\n2. Extracting persona from LinkedIn data...")
    persona_extractor = PersonaExtractor()
    
    persona_result = persona_extractor.execute(
        "",
        context={
            "linkedin_posts": EXAMPLE_LINKEDIN_POSTS,
            "linkedin_profile": EXAMPLE_LINKEDIN_PROFILE,
        }
    )
    
    if persona_result.success:
        persona_memory = persona_result.output
        print(f"✅ Persona extracted successfully!")
        print(f"   - Role: {persona_memory.role}")
        print(f"   - Expertise Areas: {', '.join(persona_memory.expertise_areas[:5])}")
        print(f"   - Voice Summary: {persona_memory.voice_summary[:100]}...")
        print(f"   - Technical Skills: {len(persona_memory.technical_skills)} skills")
        
        # Save persona memory for reuse
        persona_memory.save("persona_memory.json")
        print("\n   💾 Persona memory saved to persona_memory.json")
        
        # Option 2: Create blog with extracted persona
        print("\n3. Creating blog using extracted persona...")
        result = agent.execute(
            "Write a blog about microservices best practices",
            context={
                "persona_memory": persona_memory,  # Reuse extracted persona
            }
        )
        
        if result.success:
            deliverable = result.output
            print(f"\n✅ Blog created successfully!")
            print(f"   - Title: {deliverable.title}")
            print(f"   - Quality Score: {deliverable.quality_report.get('final_score', 'N/A')}/100")
            print(f"\n📄 Blog Preview:")
            print("-" * 70)
            print(deliverable.packaged_post[:500] + "...")
            print("-" * 70)
        else:
            print(f"\n❌ Blog creation failed: {result.error}")
    else:
        print(f"\n❌ Persona extraction failed: {persona_result.error}")
    
    # Option 3: Extract persona and create blog in one call
    print("\n\n" + "="*70)
    print("Alternative: Extract persona and create blog in one call")
    print("="*70)
    
    result2 = agent.execute(
        "Write about Kubernetes deployment strategies",
        context={
            "linkedin_posts": EXAMPLE_LINKEDIN_POSTS,
            "linkedin_profile": EXAMPLE_LINKEDIN_PROFILE,
        }
    )
    
    if result2.success:
        deliverable2 = result2.output
        print(f"\n✅ Blog created with automatic persona extraction!")
        print(f"   - Title: {deliverable2.title}")
        print(f"   - Quality Score: {deliverable2.quality_report.get('final_score', 'N/A')}/100")
    
    # Option 4: Load saved persona memory
    print("\n\n" + "="*70)
    print("Reusing saved persona memory")
    print("="*70)
    
    try:
        loaded_persona = PersonaMemory.load("persona_memory.json")
        print(f"✅ Loaded persona memory from file")
        print(f"   - Role: {loaded_persona.role}")
        print(f"   - Extraction Date: {loaded_persona.extraction_date}")
        
        # Use loaded persona for new blog
        result3 = agent.execute(
            "Write about system design principles",
            context={"persona_memory": loaded_persona}
        )
        
        if result3.success:
            print(f"\n✅ Blog created using loaded persona!")
    except FileNotFoundError:
        print("⚠️  No saved persona memory found (run previous steps first)")


if __name__ == "__main__":
    main()
