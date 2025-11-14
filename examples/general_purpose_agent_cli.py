#!/usr/bin/env python3
"""
General Purpose Agent CLI

Interactive command-line interface for the self-improving general purpose agent.
Features critique loops, progress tracking, and free tier support.
"""

import sys
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich.markdown import Markdown

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_agentic_workflow.agents import GeneralPurposeAgent
from ai_agentic_workflow.config import get_free_tier_config, get_config_by_name
from ai_agentic_workflow.logging import setup_logging


console = Console()


def print_header():
    """Print CLI header."""
    header = """
# 🤖 General Purpose Agent

**Self-improving AI with critique loops and free tier support**

Features:
- ✅ Multi-dimensional confidence scoring
- ✅ Intelligent clarification
- ✅ Deep task reasoning (2-15 tasks)
- ✅ Critique-driven quality improvement
- ✅ Up to 3 retry attempts per task
- ✅ $0/month cost (using Gemini + Groq free tiers)
"""
    console.print(Panel(Markdown(header), border_style="blue"))


def progress_callback(progress_data):
    """Callback for progress updates (can be extended for live UI)."""
    stage = progress_data.get('stage', '')
    progress_percent = progress_data.get('progress_percent', 0)

    # Simple console output (can be enhanced)
    console.print(f"[cyan]Stage:[/cyan] {stage} | [green]Progress:[/green] {progress_percent}%")


def main():
    """Run the general purpose agent CLI."""
    print_header()

    # Setup logging
    setup_logging(level="INFO", structured=False)

    # Ask user for configuration
    console.print("\n[bold cyan]Configuration Options:[/bold cyan]")
    console.print("1. Free Tier (Gemini + Groq) - $0/month [recommended]")
    console.print("2. Default (Claude + GPT) - ~$10-20/month")
    console.print("3. Accurate (Best models) - ~$20-30/month")
    console.print("4. Local (LM Studio) - $0/month (requires LM Studio running)")

    choice = console.input("\n[bold]Select configuration [1-4]:[/bold] ").strip()

    config_map = {
        '1': 'free',
        '2': 'default',
        '3': 'accurate',
        '4': 'local',
    }

    config_name = config_map.get(choice, 'free')

    try:
        config = get_config_by_name(config_name)
        console.print(f"\n✓ Using '{config_name}' configuration")

        # Show cost estimate
        if config_name == 'free':
            console.print("[green]💰 Estimated cost: $0/month (free tier)[/green]")
        elif config_name == 'default':
            console.print("[yellow]💰 Estimated cost: $10-20/month[/yellow]")
        elif config_name == 'accurate':
            console.print("[yellow]💰 Estimated cost: $20-30/month[/yellow]")
        else:
            console.print("[green]💰 Estimated cost: $0/month (local)[/green]")
    except Exception as e:
        console.print(f"[red]Error loading config:[/red] {e}")
        console.print("[yellow]Falling back to free tier config[/yellow]")
        config = get_free_tier_config()

    # Validate configuration
    errors = config.validate()
    if errors:
        console.print("\n[red]⚠️  Configuration validation warnings:[/red]")
        for error in errors:
            if "API key" in error:
                console.print(f"  [yellow]• {error}[/yellow]")
            else:
                console.print(f"  [red]• {error}[/red]")

        if any("API key" not in e for e in errors):
            console.print("\n[red]Fatal configuration errors. Exiting.[/red]")
            return 1

    # Initialize agent
    console.print("\n[cyan]Initializing agent...[/cyan]")

    try:
        agent = GeneralPurposeAgent(
            config=config,
            progress_callback=progress_callback
        )
        console.print("[green]✓ Agent initialized successfully[/green]")
    except Exception as e:
        console.print(f"[red]Failed to initialize agent:[/red] {e}")
        return 1

    # Main loop
    console.print("\n[bold green]Agent ready![/bold green] Type your request or 'quit' to exit.\n")

    while True:
        try:
            # Get user input
            user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                console.print("\n[yellow]Goodbye! 👋[/yellow]")
                break

            # Execute agent
            console.print("\n[cyan]🤖 Processing your request...[/cyan]\n")

            result = agent.execute(user_input)

            # Display result
            if result.success:
                console.print("\n[bold green]✓ Task completed successfully![/bold green]\n")

                # Display output
                output_panel = Panel(
                    Markdown(result.output),
                    title="[bold]Agent Response[/bold]",
                    border_style="green"
                )
                console.print(output_panel)

                # Display metadata
                metadata = result.metadata
                if metadata:
                    console.print(f"\n[dim]Execution time: {metadata.get('execution_time', 0):.2f}s[/dim]")
                    console.print(f"[dim]Tasks executed: {metadata.get('tasks_executed', 0)}[/dim]")

                    final_critique = metadata.get('final_critique', {})
                    if final_critique:
                        quality_score = final_critique.get('quality_score', 0)
                        console.print(f"[dim]Quality score: {quality_score:.2f}/1.00[/dim]")

            else:
                console.print(f"\n[bold red]✗ Task failed:[/bold red] {result.error}\n")

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted. Type 'quit' to exit or continue with new request.[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error:[/red] {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
