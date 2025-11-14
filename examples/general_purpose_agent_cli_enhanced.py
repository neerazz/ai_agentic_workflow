#!/usr/bin/env python3
"""
General Purpose Agent - Enhanced CLI with Live Progress

Interactive command-line interface with real-time progress tracking,
live task visualization, and conversation history management.
"""

import sys
import os
import time
from typing import Optional, Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich import box

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_agentic_workflow.agents import GeneralPurposeAgent
from ai_agentic_workflow.config import get_free_tier_config, get_config_by_name
from ai_agentic_workflow.logging import setup_logging


console = Console()

# Global progress state
current_progress = {
    'stage': 'Idle',
    'progress_percent': 0,
    'current_task': None,
    'tasks_completed': 0,
    'tasks_total': 0,
    'critique_score': None,
    'attempt': 1,
    'max_attempts': 3,
    'task_breakdown': [],
}


def generate_progress_table():
    """Generate a rich table showing current progress."""
    table = Table(
        title="🤖 Agent Progress",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )

    table.add_column("Metric", style="cyan", width=20)
    table.add_column("Status", style="green", width=50)

    # Stage
    stage = current_progress.get('stage', 'Idle')
    stage_emoji = {
        'clarifying': '❓ Clarifying',
        'planning': '📋 Planning',
        'executing': '⚙️ Executing',
        'critiquing': '🔍 Critiquing',
        'synthesizing': '✨ Synthesizing',
        'completed': '✅ Completed',
        'idle': '💤 Idle',
        'ready': '🚀 Ready',
    }
    stage_display = stage_emoji.get(stage.lower(), f'🤖 {stage}')
    table.add_row("Stage", stage_display)

    # Progress bar
    progress_percent = current_progress.get('progress_percent', 0)
    bar_length = 30
    filled = int(bar_length * progress_percent / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    table.add_row("Progress", f"{bar} {progress_percent}%")

    # Tasks
    tasks_completed = current_progress.get('tasks_completed', 0)
    tasks_total = current_progress.get('tasks_total', 0)
    if tasks_total > 0:
        table.add_row("Tasks", f"{tasks_completed}/{tasks_total} completed")

    # Current task
    current_task = current_progress.get('current_task')
    if current_task:
        task_display = current_task[:45] + '...' if len(current_task) > 45 else current_task
        table.add_row("Current Task", task_display)

    # Critique score
    critique_score = current_progress.get('critique_score')
    if critique_score is not None:
        score_color = "green" if critique_score >= 0.75 else "yellow" if critique_score >= 0.6 else "red"
        score_text = Text(f"{critique_score:.2f}/1.00", style=score_color)
        table.add_row("Quality Score", score_text)

    # Attempt
    attempt = current_progress.get('attempt', 1)
    max_attempts = current_progress.get('max_attempts', 3)
    if attempt > 1:
        table.add_row("Attempt", f"{attempt}/{max_attempts}")

    return table


def generate_task_breakdown_table():
    """Generate a table showing task breakdown."""
    task_breakdown = current_progress.get('task_breakdown', [])

    if not task_breakdown:
        return None

    table = Table(
        title="📋 Task Breakdown",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("#", style="dim", width=4)
    table.add_column("Task", style="white", width=40)
    table.add_column("Status", width=15)
    table.add_column("Score", width=8, justify="right")

    for i, task in enumerate(task_breakdown, 1):
        task_name = task.get('title', task.get('description', 'Unknown'))[:40]
        status = task.get('status', 'pending')
        score = task.get('critique_score')

        # Status emoji
        status_emoji = {
            'pending': '⏳ Pending',
            'in_progress': '🔄 Working',
            'critiquing': '🔍 Review',
            'completed': '✅ Done',
            'failed': '❌ Failed',
        }
        status_display = status_emoji.get(status, status)

        # Score display
        score_display = f"{score:.2f}" if score is not None else "-"

        table.add_row(
            str(i),
            task_name,
            status_display,
            score_display,
        )

    return table


def progress_callback(progress_data: Dict[str, Any]):
    """Update global progress state."""
    global current_progress
    current_progress.update(progress_data)


def print_header():
    """Print CLI header."""
    header = """
# 🤖 General Purpose Agent - Enhanced CLI

**Self-improving AI with real-time progress tracking**

Features:
- ✅ Live progress visualization
- ✅ Task breakdown display
- ✅ Multi-turn conversation memory
- ✅ Three-layer critique loops
- ✅ Real-time quality scoring
- ✅ Free tier support ($0/month)
"""
    console.print(Panel(Markdown(header), border_style="blue", padding=(1, 2)))


def select_configuration():
    """Interactive configuration selection."""
    console.print("\n[bold cyan]⚙️  Configuration Options:[/bold cyan]")
    console.print("  1. [green]Free Tier[/green] (Gemini + Groq) - $0/month [recommended]")
    console.print("  2. [yellow]Default[/yellow] (Claude + GPT) - ~$10-20/month")
    console.print("  3. [yellow]Accurate[/yellow] (Best models) - ~$20-30/month")
    console.print("  4. [green]Local[/green] (LM Studio) - $0/month (requires LM Studio)")

    choice = console.input("\n[bold]Select configuration [1-4, default=1]:[/bold] ").strip()

    config_map = {
        '1': ('free', '$0/month (free tier)'),
        '2': ('default', '$10-20/month'),
        '3': ('accurate', '$20-30/month'),
        '4': ('local', '$0/month (local)'),
        '': ('free', '$0/month (free tier)'),  # Default
    }

    config_name, cost_estimate = config_map.get(choice, ('free', '$0/month (free tier)'))

    return config_name, cost_estimate


def initialize_agent(config_name: str):
    """Initialize the agent with configuration."""
    console.print(f"\n[cyan]📦 Loading '{config_name}' configuration...[/cyan]")

    try:
        config = get_config_by_name(config_name)

        # Validate
        errors = config.validate()
        if errors:
            api_key_errors = [e for e in errors if "API key" in e]
            fatal_errors = [e for e in errors if "API key" not in e]

            if api_key_errors:
                console.print("\n[yellow]⚠️  API Key Warnings:[/yellow]")
                for error in api_key_errors[:3]:  # Show max 3
                    console.print(f"  [dim]• {error}[/dim]")

            if fatal_errors:
                console.print("\n[red]❌ Fatal configuration errors:[/red]")
                for error in fatal_errors:
                    console.print(f"  [red]• {error}[/red]")
                return None

        # Initialize
        agent = GeneralPurposeAgent(
            config=config,
            progress_callback=progress_callback
        )

        console.print("[green]✅ Agent initialized successfully![/green]")
        return agent

    except Exception as e:
        console.print(f"[red]❌ Failed to initialize agent:[/red] {e}")
        return None


def show_conversation_history(agent: GeneralPurposeAgent):
    """Display conversation history."""
    try:
        history = agent.get_conversation_history()

        if not history:
            console.print("\n[yellow]📝 No conversation history yet[/yellow]")
            return

        console.print("\n" + "="*70)
        console.print("[bold cyan]💬 Conversation History[/bold cyan]")
        console.print("="*70 + "\n")

        for turn in history:
            turn_id = turn.get('turn_id', '?')
            timestamp = turn.get('timestamp', '')
            user_query = turn.get('user_query', '')
            ai_response = turn.get('ai_response', '')

            console.print(f"[bold]Turn {turn_id}[/bold] - [dim]{timestamp}[/dim]")
            console.print(f"[cyan]You:[/cyan] {user_query}")
            console.print(f"[green]AI:[/green] {ai_response[:150]}{'...' if len(ai_response) > 150 else ''}")
            console.print("-" * 70 + "\n")

        console.print()

    except Exception as e:
        console.print(f"[red]❌ Error showing history:[/red] {e}")


def process_request(agent: GeneralPurposeAgent, user_input: str):
    """Process user request with live progress display."""
    global current_progress

    # Reset progress
    current_progress = {
        'stage': 'Processing',
        'progress_percent': 0,
        'current_task': user_input[:50] + '...' if len(user_input) > 50 else user_input,
        'tasks_completed': 0,
        'tasks_total': 0,
        'critique_score': None,
        'attempt': 1,
        'max_attempts': 3,
        'task_breakdown': [],
    }

    # Create layout
    layout = Layout()
    layout.split_column(
        Layout(name="progress", size=12),
        Layout(name="tasks", size=8),
    )

    with Live(layout, refresh_per_second=4, console=console):
        # Start execution
        start_time = time.time()

        try:
            result = agent.execute(user_input)
            execution_time = time.time() - start_time

            # Update final progress
            current_progress['stage'] = 'Completed'
            current_progress['progress_percent'] = 100

            # Brief delay to show final state
            time.sleep(0.5)

        except Exception as e:
            execution_time = time.time() - start_time
            current_progress['stage'] = 'Failed'
            result = type('Result', (), {'success': False, 'error': str(e), 'metadata': {}})()

        # Update layout one last time
        layout["progress"].update(generate_progress_table())
        task_table = generate_task_breakdown_table()
        if task_table:
            layout["tasks"].update(task_table)

    # Display result
    console.print("\n")

    if result.success:
        console.print(Panel(
            Markdown(result.output),
            title="[bold green]✅ Agent Response[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))

        # Metadata
        metadata = result.metadata or {}
        tasks_executed = metadata.get('tasks_executed', 0)
        final_critique = metadata.get('final_critique', {})
        quality_score = final_critique.get('quality_score', 0)

        console.print(f"\n[dim]⏱️  Execution time: {execution_time:.1f}s | "
                     f"📋 Tasks: {tasks_executed} | "
                     f"⭐ Quality: {quality_score:.2f}/1.00[/dim]\n")

    else:
        console.print(Panel(
            f"[red]{result.error}[/red]",
            title="[bold red]❌ Error[/bold red]",
            border_style="red",
        ))
        console.print()


def show_help():
    """Show help message."""
    help_text = """
[bold cyan]Available Commands:[/bold cyan]

  [green]<your question>[/green]     - Ask the agent anything
  [yellow]/history[/yellow]           - View conversation history
  [yellow]/clear[/yellow]             - Clear conversation (start fresh)
  [yellow]/help[/yellow]              - Show this help message
  [yellow]/quit[/yellow] or [yellow]/exit[/yellow]    - Exit the application

[bold cyan]Tips:[/bold cyan]

  • The agent remembers previous conversations automatically
  • Ask follow-up questions naturally (e.g., "tell me more about that")
  • Quality scores show how confident the agent is in its response
  • Critique loops automatically retry low-quality outputs (max 3 attempts)
"""
    console.print(Panel(help_text, border_style="blue", padding=(1, 2)))


def main():
    """Main CLI loop."""
    print_header()

    # Setup logging
    setup_logging(level="INFO", structured=False)

    # Configuration
    config_name, cost_estimate = select_configuration()
    console.print(f"[dim]💰 Estimated cost: {cost_estimate}[/dim]")

    # Initialize agent
    agent = initialize_agent(config_name)

    if not agent:
        console.print("\n[red]Failed to initialize agent. Exiting.[/red]")
        return 1

    # Show help
    console.print("\n[dim]Type /help for available commands[/dim]")

    # Main loop
    console.print("\n[bold green]🚀 Agent ready![/bold green] Ask me anything or type /quit to exit.\n")

    while True:
        try:
            # Get user input
            user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()

            if not user_input:
                continue

            # Commands
            if user_input.lower() in ['/quit', '/exit', '/q']:
                console.print("\n[yellow]👋 Goodbye![/yellow]\n")
                break

            elif user_input.lower() == '/help':
                show_help()
                continue

            elif user_input.lower() == '/history':
                show_conversation_history(agent)
                continue

            elif user_input.lower() == '/clear':
                agent.clear_conversation()
                console.print("\n[green]✅ Conversation cleared[/green]\n")
                continue

            # Process request
            console.print()
            process_request(agent, user_input)

        except KeyboardInterrupt:
            console.print("\n\n[yellow]⚠️  Interrupted. Type /quit to exit or continue.[/yellow]\n")

        except Exception as e:
            console.print(f"\n[red]❌ Error:[/red] {e}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
