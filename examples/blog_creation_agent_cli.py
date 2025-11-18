#!/usr/bin/env python3
"""
CLI interface for Blog Creation Agent.

Simple command-line interface to create blogs with optional user input.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai_agentic_workflow.agents import BlogCreationAgent
from src.ai_agentic_workflow.config import get_free_tier_blog_config


def main():
    parser = argparse.ArgumentParser(
        description="Create high-quality technical blog posts using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create blog with topic only
  python blog_creation_agent_cli.py --topic "Kubernetes best practices"

  # Create blog with full persona details
  python blog_creation_agent_cli.py \\
    --persona "Principal Software Engineer" \\
    --topic "Microservices architecture patterns" \\
    --goal "Teach best practices" \\
    --voice "Pragmatic mentor, data-backed"

  # Use free-form input
  python blog_creation_agent_cli.py \\
    --input "I want to write about my experience migrating from monoliths to microservices"
        """
    )

    parser.add_argument(
        "--persona",
        type=str,
        help="Author persona (e.g., 'Principal Software Engineer')"
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="Blog topic or subject"
    )
    parser.add_argument(
        "--goal",
        type=str,
        help="Blog goal (e.g., 'teach', 'inspire', 'share experience')"
    )
    parser.add_argument(
        "--voice",
        type=str,
        help="Writing voice/style (e.g., 'Pragmatic mentor, data-backed')"
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Free-form user input (alternative to structured args)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="blog_output.md",
        help="Output file path (default: blog_output.md)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full deliverable as JSON"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="free",
        choices=["free", "default"],
        help="Configuration preset (default: free)"
    )

    args = parser.parse_args()

    # Build user input
    if args.input:
        user_input = args.input
    else:
        parts = []
        if args.persona:
            parts.append(f"Persona: {args.persona}")
        if args.topic:
            parts.append(f"Topic: {args.topic}")
        if args.goal:
            parts.append(f"Goal: {args.goal}")
        if args.voice:
            parts.append(f"Voice: {args.voice}")

        if not parts:
            print("Error: Please provide either --input or at least one of --persona, --topic, --goal, --voice")
            parser.print_help()
            sys.exit(1)

        user_input = "\n".join(parts)

    print("🚀 Initializing Blog Creation Agent...")
    print(f"📝 Input: {user_input[:100]}...")

    # Initialize agent
    try:
        if args.config == "free":
            blog_config = get_free_tier_blog_config()
        else:
            from src.ai_agentic_workflow.config import get_default_config
            from src.ai_agentic_workflow.config.blog_agent_config import BlogAgentConfig
            blog_config = BlogAgentConfig()

        agent = BlogCreationAgent(config=blog_config)
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        sys.exit(1)

    # Execute blog creation
    print("\n✨ Creating blog...")
    print("⏳ This may take a few minutes...\n")

    try:
        result = agent.execute(user_input)

        if not result.success:
            print(f"❌ Blog creation failed: {result.error}")
            sys.exit(1)

        deliverable = result.output

        # Output results
        if args.json:
            # Output full JSON
            output_data = {
                "title": deliverable.title,
                "meta_description": deliverable.meta_description,
                "seo_keywords": deliverable.seo_keywords,
                "packaged_post": deliverable.packaged_post,
                "quality_report": deliverable.quality_report,
                "visual_storyboard": deliverable.visual_storyboard,
                "promo_bundle": deliverable.promo_bundle,
                "knowledge_transfer_kit": deliverable.knowledge_transfer_kit,
                "metadata": deliverable.metadata,
            }
            output_path = args.output.replace(".md", ".json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Full deliverable saved to {output_path}")
        else:
            # Output markdown blog post
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(f"# {deliverable.title}\n\n")
                f.write(f"*{deliverable.meta_description}*\n\n")
                f.write("---\n\n")
                f.write(deliverable.packaged_post)
            print(f"✅ Blog saved to {args.output}")

        # Print summary
        print("\n" + "="*70)
        print("BLOG CREATION SUMMARY")
        print("="*70)
        print(f"Title: {deliverable.title}")
        print(f"Quality Score: {deliverable.quality_report.get('final_score', 'N/A')}/100")
        print(f"SEO Score: {deliverable.quality_report.get('seo_score', 'N/A')}")
        print(f"Brand Score: {deliverable.quality_report.get('brand_score', 'N/A')}")
        print(f"Word Count: ~{len(deliverable.packaged_post.split())} words")
        print("="*70)

        # Print promo bundle preview
        if deliverable.promo_bundle:
            print("\n📢 PROMO BUNDLE PREVIEW")
            print("-"*70)
            if "tldr" in deliverable.promo_bundle:
                print(f"TL;DR: {deliverable.promo_bundle['tldr'][:200]}...")
            if "linkedin_hook" in deliverable.promo_bundle:
                print(f"\nLinkedIn Hook:\n{deliverable.promo_bundle['linkedin_hook'][:200]}...")
            print("-"*70)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during blog creation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
