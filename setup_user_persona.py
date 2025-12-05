#!/usr/bin/env python3
"""
Setup User Persona - Fetch LinkedIn data and establish persona.

This script:
1. Fetches LinkedIn profile and posts from your LinkedIn URL
2. Extracts comprehensive persona information
3. Saves persona memory for future use
4. Establishes it as the default persona for blog creation
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Rich not available - using basic output\n")

from src.ai_agentic_workflow.agents import (
    LinkedInDataFetcher,
    PersonaExtractor,
    PersonaMemory
)
from src.ai_agentic_workflow.config import get_free_tier_config


# Your LinkedIn profile
LINKEDIN_URL = "https://www.linkedin.com/in/neerajkumarsinghb/"
PERSONA_MEMORY_FILE = "neeraj_persona_memory.json"
CACHE_DIR = ".linkedin_cache"


def main():
    console = Console() if RICH_AVAILABLE else None
    
    if console:
        console.print(Panel.fit(
            "[bold blue]User Persona Setup - Neeraj Kumar Singh[/bold blue]",
            border_style="blue"
        ))
    else:
        print("="*70)
        print("User Persona Setup - Neeraj Kumar Singh")
        print("="*70)
    
    # Step 1: Fetch LinkedIn Data
    if console:
        console.print("\n[cyan]Step 1: Fetching LinkedIn data...[/cyan]")
    else:
        print("\nStep 1: Fetching LinkedIn data...")
    
    try:
        fetcher = LinkedInDataFetcher(cache_dir=CACHE_DIR)
        
        if console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Fetching profile and posts...", total=None)
                linkedin_data = fetcher.fetch_linkedin_data(
                    profile_url=LINKEDIN_URL,
                    refresh=True  # Force fresh fetch
                )
                progress.update(task, completed=True)
        else:
            print("Fetching profile and posts...")
            linkedin_data = fetcher.fetch_linkedin_data(
                profile_url=LINKEDIN_URL,
                refresh=True
            )
        
        if not linkedin_data:
            if console:
                console.print("[red]✗ Failed to fetch LinkedIn data[/red]")
                console.print("[yellow]Check PERPLEXITY_API_KEY and try again[/yellow]")
            else:
                print("✗ Failed to fetch LinkedIn data")
                print("Check PERPLEXITY_API_KEY and try again")
            return
        
        if console:
            console.print("[green]✓ LinkedIn data fetched successfully[/green]")
            if "linkedin_posts" in linkedin_data:
                console.print(f"  - Posts: {len(linkedin_data['linkedin_posts'])}")
            if "linkedin_profile" in linkedin_data:
                console.print(f"  - Profile: {len(linkedin_data['linkedin_profile'])} chars")
            if "resume" in linkedin_data:
                console.print(f"  - Resume: {len(linkedin_data['resume'])} chars")
        else:
            print("✓ LinkedIn data fetched successfully")
            if "linkedin_posts" in linkedin_data:
                print(f"  - Posts: {len(linkedin_data['linkedin_posts'])}")
            if "linkedin_profile" in linkedin_data:
                print(f"  - Profile: {len(linkedin_data['linkedin_profile'])} chars")
    
    except Exception as e:
        if console:
            console.print(f"[red]✗ Error fetching LinkedIn data: {e}[/red]")
        else:
            print(f"✗ Error fetching LinkedIn data: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Extract Persona
    if console:
        console.print("\n[cyan]Step 2: Extracting persona from LinkedIn data...[/cyan]")
    else:
        print("\nStep 2: Extracting persona from LinkedIn data...")
    
    try:
        config = get_free_tier_config()
        persona_extractor = PersonaExtractor(config=config)
        
        if console:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Analyzing profile, posts, and experience...", total=None)
                persona_result = persona_extractor.execute("", context=linkedin_data)
                progress.update(task, completed=True)
        else:
            print("Analyzing profile, posts, and experience...")
            persona_result = persona_extractor.execute("", context=linkedin_data)
        
        if not persona_result.success:
            if console:
                console.print(f"[red]✗ Persona extraction failed: {persona_result.error}[/red]")
            else:
                print(f"✗ Persona extraction failed: {persona_result.error}")
            return
        
        persona_memory = persona_result.output
        
        if console:
            console.print("[green]✓ Persona extracted successfully[/green]")
        else:
            print("✓ Persona extracted successfully")
    
    except Exception as e:
        if console:
            console.print(f"[red]✗ Error extracting persona: {e}[/red]")
        else:
            print(f"✗ Error extracting persona: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Save Persona Memory
    if console:
        console.print(f"\n[cyan]Step 3: Saving persona memory to {PERSONA_MEMORY_FILE}...[/cyan]")
    else:
        print(f"\nStep 3: Saving persona memory to {PERSONA_MEMORY_FILE}...")
    
    try:
        persona_memory.save(PERSONA_MEMORY_FILE)
        if console:
            console.print(f"[green]✓ Persona memory saved[/green]")
        else:
            print(f"✓ Persona memory saved")
    except Exception as e:
        if console:
            console.print(f"[red]✗ Error saving persona: {e}[/red]")
        else:
            print(f"✗ Error saving persona: {e}")
        return
    
    # Step 4: Display Extracted Persona
    if console:
        console.print("\n[bold cyan]Extracted Persona Summary[/bold cyan]")
        console.print("="*70)
        
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_row("[bold]Role:[/bold]", persona_memory.role or "Not specified")
        table.add_row("[bold]Years Experience:[/bold]", str(persona_memory.years_experience) if persona_memory.years_experience else "Not specified")
        table.add_row("[bold]Expertise Areas:[/bold]", ", ".join(persona_memory.expertise_areas[:10]) if persona_memory.expertise_areas else "Not specified")
        table.add_row("[bold]Technical Skills:[/bold]", str(len(persona_memory.technical_skills)) + " skills")
        table.add_row("[bold]Career Highlights:[/bold]", str(len(persona_memory.career_highlights)) + " highlights")
        table.add_row("[bold]Project Experiences:[/bold]", str(len(persona_memory.project_experiences)) + " projects")
        table.add_row("[bold]Brand Pillars:[/bold]", ", ".join(persona_memory.brand_pillars) if persona_memory.brand_pillars else "Not specified")
        table.add_row("[bold]Mentorship Style:[/bold]", persona_memory.mentorship_style or "Not specified")
        
        console.print(table)
        console.print("="*70)
        
        if persona_memory.voice_summary:
            console.print("\n[bold]Voice Summary:[/bold]")
            console.print(Panel(persona_memory.voice_summary, border_style="cyan"))
        
        if persona_memory.expertise_summary:
            console.print("\n[bold]Expertise Summary:[/bold]")
            console.print(Panel(persona_memory.expertise_summary, border_style="cyan"))
        
        if persona_memory.story_bank_summary:
            console.print("\n[bold]Story Bank Summary:[/bold]")
            console.print(Panel(persona_memory.story_bank_summary, border_style="cyan"))
        
        if persona_memory.common_phrases:
            console.print("\n[bold]Common Phrases:[/bold]")
            console.print(", ".join(persona_memory.common_phrases[:10]))
        
        if persona_memory.storytelling_patterns:
            console.print("\n[bold]Storytelling Patterns:[/bold]")
            console.print(", ".join(persona_memory.storytelling_patterns[:5]))
    
    else:
        print("\n" + "="*70)
        print("Extracted Persona Summary")
        print("="*70)
        print(f"Role: {persona_memory.role or 'Not specified'}")
        print(f"Years Experience: {persona_memory.years_experience or 'Not specified'}")
        print(f"Expertise Areas: {', '.join(persona_memory.expertise_areas[:10]) if persona_memory.expertise_areas else 'Not specified'}")
        print(f"Technical Skills: {len(persona_memory.technical_skills)} skills")
        print(f"Career Highlights: {len(persona_memory.career_highlights)} highlights")
        print(f"Project Experiences: {len(persona_memory.project_experiences)} projects")
        print(f"Brand Pillars: {', '.join(persona_memory.brand_pillars) if persona_memory.brand_pillars else 'Not specified'}")
        print(f"Mentorship Style: {persona_memory.mentorship_style or 'Not specified'}")
        print("="*70)
        
        if persona_memory.voice_summary:
            print(f"\nVoice Summary:\n{persona_memory.voice_summary}")
        if persona_memory.expertise_summary:
            print(f"\nExpertise Summary:\n{persona_memory.expertise_summary}")
        if persona_memory.story_bank_summary:
            print(f"\nStory Bank Summary:\n{persona_memory.story_bank_summary}")
    
    # Step 5: Create default config file
    if console:
        console.print(f"\n[cyan]Step 4: Creating default persona configuration...[/cyan]")
    else:
        print(f"\nStep 4: Creating default persona configuration...")
    
    try:
        default_config = {
            "default_persona_memory_file": PERSONA_MEMORY_FILE,
            "linkedin_url": LINKEDIN_URL,
            "cache_dir": CACHE_DIR,
            "persona_established": True,
            "established_date": persona_memory.extraction_date,
        }
        
        config_file = Path("persona_config.json")
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        if console:
            console.print(f"[green]✓ Default persona configuration saved to {config_file}[/green]")
        else:
            print(f"✓ Default persona configuration saved to {config_file}")
    
    except Exception as e:
        if console:
            console.print(f"[yellow]⚠ Warning: Could not save config: {e}[/yellow]")
        else:
            print(f"⚠ Warning: Could not save config: {e}")
    
    # Final summary
    if console:
        console.print("\n[bold green]✓ Persona Setup Complete![/bold green]")
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Use this persona for blog creation:")
        console.print(f"   python examples/blog_creation_agent_cli_enhanced.py \\")
        console.print(f"     --topic 'Your topic' \\")
        console.print(f"     --persona-memory {PERSONA_MEMORY_FILE}")
        console.print("\n2. Or use automatically (system will detect cached data):")
        console.print(f"   python examples/blog_creation_agent_cli_enhanced.py \\")
        console.print(f"     --topic 'Your topic'")
        console.print("\n3. Refresh persona when you have new posts:")
        console.print(f"   python setup_user_persona.py")
    else:
        print("\n✓ Persona Setup Complete!")
        print("\nNext Steps:")
        print(f"1. Use this persona for blog creation:")
        print(f"   python examples/blog_creation_agent_cli_enhanced.py --topic 'Your topic' --persona-memory {PERSONA_MEMORY_FILE}")
        print(f"\n2. Or use automatically (system will detect cached data):")
        print(f"   python examples/blog_creation_agent_cli_enhanced.py --topic 'Your topic'")
        print(f"\n3. Refresh persona when you have new posts:")
        print(f"   python setup_user_persona.py")


if __name__ == "__main__":
    main()
