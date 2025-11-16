#!/usr/bin/env python3
"""
General Purpose Agent - Gradio Web UI

Beautiful web-based chat interface with real-time progress tracking,
conversation history, and critique loop visualization.
"""

import os
import sys
import time
from typing import List

import gradio as gr

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ai_agentic_workflow.agents import GeneralPurposeAgent
from ai_agentic_workflow.config import get_free_tier_config, get_config_by_name
from ai_agentic_workflow.logging import setup_logging


# Global state
agent = None
current_progress = {
    'stage': 'Idle',
    'progress_percent': 0,
    'current_task': None,
    'tasks_completed': 0,
    'tasks_total': 0,
    'critique_score': None,
    'attempt': 1,
    'max_attempts': 3,
}


def progress_callback(progress_data):
    """Update global progress state."""
    global current_progress
    current_progress.update(progress_data)


def format_progress_display():
    """Format current progress as markdown."""
    stage = current_progress.get('stage', 'Idle')
    progress_percent = current_progress.get('progress_percent', 0)
    current_task = current_progress.get('current_task', '')
    tasks_completed = current_progress.get('tasks_completed', 0)
    tasks_total = current_progress.get('tasks_total', 0)
    critique_score = current_progress.get('critique_score')
    attempt = current_progress.get('attempt', 1)
    max_attempts = current_progress.get('max_attempts', 3)

    # Stage emoji mapping
    stage_emoji = {
        'clarifying': '❓',
        'planning': '📋',
        'executing': '⚙️',
        'critiquing': '🔍',
        'synthesizing': '✨',
        'completed': '✅',
    }

    emoji = stage_emoji.get(stage.lower(), '🤖')

    progress_md = f"### {emoji} Stage: {stage}\n\n"

    # Progress bar
    bar_length = 20
    filled = int(bar_length * progress_percent / 100)
    bar = '█' * filled + '░' * (bar_length - filled)
    progress_md += f"**Progress:** `{bar}` {progress_percent}%\n\n"

    # Task info
    if tasks_total > 0:
        progress_md += f"**Tasks:** {tasks_completed}/{tasks_total} completed\n\n"

    if current_task:
        progress_md += f"**Current:** {current_task}\n\n"

    # Critique info
    if critique_score is not None:
        score_color = "🟢" if critique_score >= 0.75 else "🟡" if critique_score >= 0.6 else "🔴"
        progress_md += f"**Quality Score:** {score_color} {critique_score:.2f}/1.00\n\n"

    if attempt > 1:
        progress_md += f"**Attempt:** {attempt}/{max_attempts}\n\n"

    return progress_md


def initialize_agent(config_choice: str):
    """Initialize the agent with selected configuration."""
    global agent, current_progress

    config_map = {
        'Free Tier (Gemini + Groq) - $0/month': 'free',
        'Default (Claude + GPT) - $10-20/month': 'default',
        'Accurate (Best models) - $20-30/month': 'accurate',
        'Local (LM Studio) - $0/month': 'local',
    }

    config_name = config_map.get(config_choice, 'free')

    try:
        # Setup logging
        setup_logging(level="INFO", structured=False)

        config = get_config_by_name(config_name)

        # Validate
        errors = config.validate()
        api_key_errors = [e for e in errors if "API key" in e]
        fatal_errors = [e for e in errors if "API key" not in e]

        if fatal_errors:
            return f"❌ Configuration errors:\n" + "\n".join(f"- {e}" for e in fatal_errors)

        # Initialize agent
        agent = GeneralPurposeAgent(
            config=config,
            progress_callback=progress_callback
        )

        # Reset progress
        current_progress = {
            'stage': 'Ready',
            'progress_percent': 0,
            'current_task': None,
            'tasks_completed': 0,
            'tasks_total': 0,
            'critique_score': None,
            'attempt': 1,
            'max_attempts': 3,
        }

        msg = f"✅ Agent initialized with **{config_name}** configuration\n\n"

        if api_key_errors:
            msg += "⚠️ Some API keys not set (will fail if used):\n"
            msg += "\n".join(f"- {e}" for e in api_key_errors)

        return msg

    except Exception as e:
        return f"❌ Failed to initialize agent: {str(e)}"


def chat_with_agent(message: str, history: List):
    """Process user message and return response."""
    global agent, current_progress

    if not agent:
        history.append({"role": "user", "content": message})
        history.append(
            {"role": "assistant", "content": "❌ Please initialize the agent first using the Configuration panel."})
        return history, format_progress_display()

    if not message.strip():
        return history, format_progress_display()

    # Add user message to history
    history.append({"role": "user", "content": message})

    # Reset progress
    current_progress.update({
        'stage': 'Processing',
        'progress_percent': 0,
        'current_task': message[:50] + '...' if len(message) > 50 else message,
        'tasks_completed': 0,
        'tasks_total': 0,
        'critique_score': None,
        'attempt': 1,
    })

    try:
        # Execute agent
        start_time = time.time()
        result = agent.execute(message)
        execution_time = time.time() - start_time

        if result.success:
            # Format response with metadata
            response = result.output

            # Add metadata footer
            metadata = result.metadata or {}
            tasks_executed = metadata.get('tasks_executed', 0)
            final_critique = metadata.get('final_critique', {})
            quality_score = final_critique.get('quality_score', 0)

            footer = f"\n\n---\n"
            footer += f"⏱️ *{execution_time:.1f}s* | "
            footer += f"📋 *{tasks_executed} tasks* | "
            footer += f"⭐ *Quality: {quality_score:.2f}/1.00*"

            response += footer

            # Update progress to completed
            current_progress.update({
                'stage': 'Completed',
                'progress_percent': 100,
                'current_task': None,
                'critique_score': quality_score,
            })

        else:
            response = f"❌ **Error:** {result.error}"
            current_progress.update({
                'stage': 'Failed',
                'progress_percent': 0,
            })

        # Add assistant response to history
        history.append({"role": "assistant", "content": response})

        return history, format_progress_display()

    except Exception as e:
        error_response = f"❌ **Exception occurred:** {str(e)}"
        current_progress.update({
            'stage': 'Failed',
            'progress_percent': 0,
        })
        history.append({"role": "assistant", "content": error_response})
        return history, format_progress_display()


def clear_conversation():
    """Clear conversation history."""
    global agent, current_progress

    if agent:
        agent.clear_conversation()

    current_progress = {
        'stage': 'Ready',
        'progress_percent': 0,
        'current_task': None,
        'tasks_completed': 0,
        'tasks_total': 0,
        'critique_score': None,
        'attempt': 1,
        'max_attempts': 3,
    }

    return [], format_progress_display()


def get_conversation_history():
    """Get formatted conversation history."""
    global agent

    if not agent:
        return "❌ Agent not initialized"

    try:
        history = agent.get_conversation_history()

        if not history:
            return "📝 No conversation history yet"

        formatted = "# 💬 Conversation History\n\n"

        for turn in history:
            turn_id = turn.get('turn_id', '?')
            timestamp = turn.get('timestamp', '')
            user_query = turn.get('user_query', '')
            ai_response = turn.get('ai_response', '')

            formatted += f"## Turn {turn_id}\n"
            formatted += f"*{timestamp}*\n\n"
            formatted += f"**You:** {user_query}\n\n"
            formatted += f"**AI:** {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}\n\n"
            formatted += "---\n\n"

        return formatted

    except Exception as e:
        return f"❌ Error getting history: {str(e)}"


def create_ui():
    """Create and launch Gradio UI."""

    with gr.Blocks(
        title="General Purpose Agent - Self-Improving AI",
        theme=gr.themes.Soft(),
    ) as demo:

        gr.Markdown("""
        # 🤖 General Purpose Agent

        **Self-improving AI with critique loops and conversation memory**

        Features: Multi-turn conversations • Task planning critique • Execution critique • Final synthesis critique • Free tier support
        """)

        with gr.Row():
            # Left column: Chat interface
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="💬 Conversation",
                    height=500,
                    show_label=True,
                    type='messages',
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Your message",
                        placeholder="Ask me anything...",
                        lines=2,
                        scale=4,
                    )
                    send_btn = gr.Button("Send 📤", variant="primary", scale=1)

                with gr.Row():
                    clear_btn = gr.Button("Clear Chat 🗑️", size="sm")
                    history_btn = gr.Button("View History 📜", size="sm")

            # Right column: Configuration and progress
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Configuration")

                config_choice = gr.Radio(
                    choices=[
                        'Free Tier (Gemini + Groq) - $0/month',
                        'Default (Claude + GPT) - $10-20/month',
                        'Accurate (Best models) - $20-30/month',
                        'Local (LM Studio) - $0/month',
                    ],
                    value='Free Tier (Gemini + Groq) - $0/month',
                    label="Select Configuration",
                )

                init_btn = gr.Button("Initialize Agent 🚀", variant="primary")
                init_status = gr.Markdown("⚠️ Agent not initialized")

                gr.Markdown("---")
                gr.Markdown("### 📊 Real-Time Progress")

                progress_display = gr.Markdown(format_progress_display())

        # History modal
        with gr.Row():
            history_display = gr.Markdown(visible=False)

        # Event handlers
        init_btn.click(
            initialize_agent,
            inputs=[config_choice],
            outputs=[init_status],
        )

        def chat_and_update(message, history):
            """Chat and continuously update progress."""
            result_history, result_progress = chat_with_agent(message, history)
            return result_history, result_progress, ""

        send_btn.click(
            chat_and_update,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, progress_display, msg_input],
        )

        msg_input.submit(
            chat_and_update,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, progress_display, msg_input],
        )

        clear_btn.click(
            clear_conversation,
            outputs=[chatbot, progress_display],
        )

        history_btn.click(
            get_conversation_history,
            outputs=[history_display],
        ).then(
            lambda: gr.update(visible=True),
            outputs=[history_display],
        )

    return demo


def main():
    """Launch the Gradio UI."""
    print("\n" + "="*60)
    print("🚀 Launching General Purpose Agent - Gradio Web UI")
    print("="*60 + "\n")

    demo = create_ui()

    # Launch with sharing disabled by default
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()
