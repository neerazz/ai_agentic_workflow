#!/usr/bin/env python3
"""
Enhanced CLI interface for Blog Creation Agent with progress tracking.

Features:
- Progress telemetry with rich output
- LinkedIn persona extraction support
- Resume/Profile input support
- Real-time quality metrics
- Detailed output options
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Rich library not available. Install with: pip install rich")
    print("   Falling back to basic output...\n")

from src.ai_agentic_workflow.agents import BlogCreationAgent, PersonaExtractor, PersonaMemory
from src.ai_agentic_workflow.config import get_free_tier_blog_config


def load_linkedin_data(posts_file: Optional[str], profile_file: Optional[str], resume_file: Optional[str]) -> dict:
    """Load LinkedIn data from files."""
    data = {}
    
    if posts_file:
        try:
            with open(posts_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Try JSON first, then plain text (one post per line)
                try:
                    posts_data = json.loads(content)
                    if isinstance(posts_data, list):
                        data["linkedin_posts"] = posts_data
                    elif isinstance(posts_data, dict) and "posts" in posts_data:
                        data["linkedin_posts"] = posts_data["posts"]
                except json.JSONDecodeError:
                    # Plain text, split by lines
                    data["linkedin_posts"] = [line.strip() for line in content.split('\n') if line.strip()]
        except FileNotFoundError:
            print(f"⚠️  Posts file not found: {posts_file}")
    
    if profile_file:
        try:
            with open(profile_file, 'r', encoding='utf-8') as f:
                data["linkedin_profile"] = f.read()
        except FileNotFoundError:
            print(f"⚠️  Profile file not found: {profile_file}")
    
    if resume_file:
        try:
            with open(resume_file, 'r', encoding='utf-8') as f:
                data["resume"] = f.read()
        except FileNotFoundError:
            print(f"⚠️  Resume file not found: {resume_file}")
    
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Create high-quality technical blog posts using AI (Enhanced CLI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple topic
  python blog_creation_agent_cli_enhanced.py --topic "Kubernetes best practices"

  # With persona details
  python blog_creation_agent_cli_enhanced.py \\
    --persona "Principal Software Engineer" \\
    --topic "Microservices architecture patterns" \\
    --goal "Teach best practices"

  # With LinkedIn data for persona extraction
  python blog_creation_agent_cli_enhanced.py \\
    --topic "Docker containerization" \\
    --linkedin-posts linkedin_posts.txt \\
    --linkedin-profile linkedin_profile.txt \\
    --resume resume.txt

  # Load saved persona memory
  python blog_creation_agent_cli_enhanced.py \\
    --topic "System design" \\
    --persona-memory my_persona.json
        """
    )

    # Input options
    parser.add_argument(
        "--persona",
        type=str,
        help="Author persona (e.g., 'Principal Software Engineer')"
    )
    parser.add_argument(
        "--topic",
        type=str,
        required=True,
        help="Blog topic or subject (required)"
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

    # LinkedIn/Resume data
    parser.add_argument(
        "--linkedin-posts",
        type=str,
        help="Path to file containing LinkedIn posts (JSON array or one per line)"
    )
    parser.add_argument(
        "--linkedin-profile",
        type=str,
        help="Path to file containing LinkedIn profile text"
    )
    parser.add_argument(
        "--resume",
        type=str,
        help="Path to file containing resume text"
    )
    parser.add_argument(
        "--persona-memory",
        type=str,
        help="Path to saved persona memory JSON file"
    )

    # Output options
    parser.add_argument(
        "--output",
        type=str,
        default="blog_output.md",
        help="Output file path for blog (default: blog_output.md)"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Output file path for full JSON deliverable"
    )
    parser.add_argument(
        "--output-persona",
        type=str,
        help="Save extracted persona memory to this file"
    )

    # Configuration
    parser.add_argument(
        "--config",
        type=str,
        default="free",
        choices=["free", "default"],
        help="Configuration preset (default: free)"
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress output"
    )

    args = parser.parse_args()

    # Initialize console
    console = Console() if RICH_AVAILABLE else None

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

        user_input = "\n".join(parts) if parts else args.topic

    # Display header
    if console:
        console.print(Panel.fit(
            "[bold blue]Blog Creation Agent - Enhanced CLI[/bold blue]",
            border_style="blue"
        ))
    else:
        print("="*70)
        print("Blog Creation Agent - Enhanced CLI")
        print("="*70)

    # Load LinkedIn data if provided
    context = {}
    if args.linkedin_posts or args.linkedin_profile or args.resume:
        if console:
            console.print("\n[cyan]Loading LinkedIn data...[/cyan]")
        else:
            print("\nLoading LinkedIn data...")
        
        linkedin_data = load_linkedin_data(
            args.linkedin_posts,
            args.linkedin_profile,
            args.resume
        )
        context.update(linkedin_data)
        
        if linkedin_data:
            if console:
                console.print(f"[green]✓[/green] Loaded LinkedIn data")
                if "linkedin_posts" in linkedin_data:
                    console.print(f"  - Posts: {len(linkedin_data['linkedin_posts'])}")
                if "linkedin_profile" in linkedin_data:
                    console.print(f"  - Profile: {len(linkedin_data['linkedin_profile'])} chars")
                if "resume" in linkedin_data:
                    console.print(f"  - Resume: {len(linkedin_data['resume'])} chars")
            else:
                print(f"✓ Loaded LinkedIn data")

    # Load persona memory if provided
    if args.persona_memory:
        try:
            persona_memory = PersonaMemory.load(args.persona_memory)
            context["persona_memory"] = persona_memory
            if console:
                console.print(f"[green]✓[/green] Loaded persona memory from {args.persona_memory}")
            else:
                print(f"✓ Loaded persona memory from {args.persona_memory}")
        except Exception as e:
            if console:
                console.print(f"[red]✗[/red] Failed to load persona memory: {e}")
            else:
                print(f"✗ Failed to load persona memory: {e}")

    # Initialize agent
    if console:
        console.print("\n[cyan]Initializing Blog Creation Agent...[/cyan]")
    else:
        print("\nInitializing Blog Creation Agent...")

    try:
        if args.config == "free":
            blog_config = get_free_tier_blog_config()
        else:
            from src.ai_agentic_workflow.config import get_default_config
            from src.ai_agentic_workflow.config.blog_agent_config import BlogAgentConfig
            blog_config = BlogAgentConfig()

        agent = BlogCreationAgent(config=blog_config)
        
        if console:
            console.print("[green]✓[/green] Agent initialized")
        else:
            print("✓ Agent initialized")
    except Exception as e:
        if console:
            console.print(f"[red]✗[/red] Failed to initialize agent: {e}")
        else:
            print(f"✗ Failed to initialize agent: {e}")
        sys.exit(1)

    # Execute blog creation
    if console:
        console.print(f"\n[cyan]Creating blog:[/cyan] [yellow]{args.topic}[/yellow]")
        console.print("⏳ This may take a few minutes...\n")
    else:
        print(f"\nCreating blog: {args.topic}")
        print("⏳ This may take a few minutes...\n")

    try:
        # Show progress if rich is available and not disabled
        if console and not args.no_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Creating blog...", total=None)
                result = agent.execute(user_input, context=context)
                progress.update(task, completed=True)
        else:
            result = agent.execute(user_input, context=context)

        if not result.success:
            if console:
                console.print(f"\n[red]✗ Blog creation failed:[/red] {result.error}")
            else:
                print(f"\n✗ Blog creation failed: {result.error}")
            sys.exit(1)

        deliverable = result.output

        # Save persona memory if extracted
        if agent.persona_memory and args.output_persona:
            agent.persona_memory.save(args.output_persona)
            if console:
                console.print(f"[green]✓[/green] Persona memory saved to {args.output_persona}")
            else:
                print(f"✓ Persona memory saved to {args.output_persona}")

        # Output results
        if args.output_json:
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
            with open(args.output_json, "w", encoding="utf-8") as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            if console:
                console.print(f"[green]✓[/green] Full deliverable saved to {args.output_json}")
            else:
                print(f"✓ Full deliverable saved to {args.output_json}")

        # Save markdown blog
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(f"# {deliverable.title}\n\n")
            f.write(f"*{deliverable.meta_description}*\n\n")
            f.write("---\n\n")
            f.write(deliverable.packaged_post)
        
        if console:
            console.print(f"[green]✓[/green] Blog saved to {args.output}")

        # Display summary
        if console:
            console.print("\n" + "="*70)
            console.print("[bold green]BLOG CREATION SUMMARY[/bold green]")
            console.print("="*70)
            
            # Create summary table
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_row("[bold]Title:[/bold]", deliverable.title)
            table.add_row("[bold]Quality Score:[/bold]", f"{deliverable.quality_report.get('final_score', 'N/A')}/100")
            table.add_row("[bold]SEO Score:[/bold]", str(deliverable.quality_report.get('seo_score', 'N/A')))
            table.add_row("[bold]Brand Score:[/bold]", str(deliverable.quality_report.get('brand_score', 'N/A')))
            table.add_row("[bold]Word Count:[/bold]", f"~{len(deliverable.packaged_post.split())} words")
            if result.metadata.get('persona_used'):
                table.add_row("[bold]Persona:[/bold]", "[green]✓ Extracted and used[/green]")
            
            console.print(table)
            console.print("="*70)

            # Promo bundle preview
            if deliverable.promo_bundle:
                console.print("\n[bold cyan]📢 PROMO BUNDLE PREVIEW[/bold cyan]")
                console.print("-"*70)
                if "tldr" in deliverable.promo_bundle:
                    console.print(f"[bold]TL;DR:[/bold] {deliverable.promo_bundle['tldr'][:200]}...")
                if "linkedin_hook" in deliverable.promo_bundle:
                    console.print(f"\n[bold]LinkedIn Hook:[/bold]")
                    console.print(deliverable.promo_bundle['linkedin_hook'][:200] + "...")
                console.print("-"*70)
        else:
            # Basic output
            print("\n" + "="*70)
            print("BLOG CREATION SUMMARY")
            print("="*70)
            print(f"Title: {deliverable.title}")
            print(f"Quality Score: {deliverable.quality_report.get('final_score', 'N/A')}/100")
            print(f"SEO Score: {deliverable.quality_report.get('seo_score', 'N/A')}")
            print(f"Brand Score: {deliverable.quality_report.get('brand_score', 'N/A')}")
            print(f"Word Count: ~{len(deliverable.packaged_post.split())} words")
            if result.metadata.get('persona_used'):
                print("Persona: ✓ Extracted and used")
            print("="*70)

    except KeyboardInterrupt:
        if console:
            console.print("\n\n[yellow]⚠️  Interrupted by user[/yellow]")
        else:
            print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        if console:
            console.print(f"\n[red]✗ Error during blog creation:[/red] {e}")
        else:
            print(f"\n✗ Error during blog creation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
