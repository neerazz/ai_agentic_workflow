"""
Example script to run the blog creation workflow.
"""

import logging
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.ai_agentic_workflow.workflows.blog_creation_workflow import run_blog_creation_workflow

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main() -> None:

    print("Starting blog creation workflow...")
    print("=" * 60)

    linkedin_url = "https://www.linkedin.com/in/sarah-chen/"

    try:
        result = run_blog_creation_workflow(
            linkedin_profile_data=None,
            linkedin_profile_url=linkedin_url,
        )

        print("\n✅ Blog Creation Successful!")
        print(f"📊 Final Score: {result['final_score']}/100")
        print(f"🔄 Attempts: {result['attempts']}")
        print(f"📝 Selected Topic: {result['selected_topic'].get('topic', 'N/A')}")
        print(f"📚 Category: {result['selected_topic'].get('category', 'N/A')}")

        print("\n" + "=" * 60)
        print("📄 FINAL BLOG")
        print("=" * 60)
        print(result['final_blog'])

        output_dir = Path("output/blogs")
        output_dir.mkdir(parents=True, exist_ok=True)
        topic = result['selected_topic'].get('topic', 'blog')
        filename = f"{topic.lower().replace(' ', '_')[:50]}.md"
        filepath = output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result['final_blog'])

        print(f"\n💾 Blog saved to: {filepath}")

        if result.get('community_resources'):
            print("\n🌐 Community Resources:")
            for ref in result['community_resources'].get('integrated_references', []):
                print(f"  - {ref['resource']}: {ref['url']}")

    except Exception as e:  # pragma: no cover - runtime issues
        print(f"\n❌ Error: {e}")
        logging.error("Blog creation failed", exc_info=True)


if __name__ == "__main__":
    main()
