#!/usr/bin/env python3
"""
Gradio UI for Blog Creation Agent.

Interactive web interface for creating blogs with optional user input.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import gradio as gr
from src.ai_agentic_workflow.agents import BlogCreationAgent
from src.ai_agentic_workflow.config import get_free_tier_blog_config


def create_blog(
    user_input: str,
    persona: str,
    topic: str,
    goal: str,
    voice: str,
    progress=gr.Progress()
) -> tuple:
    """
    Create blog using the Blog Creation Agent.

    Args:
        user_input: Free-form input
        persona: Author persona
        topic: Blog topic
        goal: Blog goal
        voice: Writing voice
        progress: Gradio progress tracker

    Returns:
        Tuple of (blog_markdown, quality_report, promo_bundle)
    """
    # Build input string
    if user_input.strip():
        input_text = user_input
    else:
        parts = []
        if persona:
            parts.append(f"Persona: {persona}")
        if topic:
            parts.append(f"Topic: {topic}")
        if goal:
            parts.append(f"Goal: {goal}")
        if voice:
            parts.append(f"Voice: {voice}")

        if not parts:
            return (
                "❌ Error: Please provide either free-form input or at least one field (persona, topic, goal, voice)",
                "",
                ""
            )

        input_text = "\n".join(parts)

    try:
        progress(0.1, desc="Initializing agent...")
        agent = BlogCreationAgent(config=get_free_tier_blog_config())

        progress(0.2, desc="Creating blog...")
        result = agent.execute(input_text)

        if not result.success:
            return (
                f"❌ Blog creation failed: {result.error}",
                "",
                ""
            )

        deliverable = result.output

        progress(0.9, desc="Formatting output...")

        # Format quality report
        quality_report = f"""# Quality Report

## Overall Score: {deliverable.quality_report.get('final_score', 'N/A')}/100

### Detailed Scores:
- SEO Score: {deliverable.quality_report.get('seo_score', 'N/A')}
- Brand Score: {deliverable.quality_report.get('brand_score', 'N/A')}

### Critique Details:
```json
{json.dumps(deliverable.quality_report.get('critique_details', {}), indent=2)}
```
"""

        # Format promo bundle
        promo_text = "## Promo Bundle\n\n"
        if deliverable.promo_bundle:
            if "tldr" in deliverable.promo_bundle:
                promo_text += f"### TL;DR\n{deliverable.promo_bundle['tldr']}\n\n"
            if "linkedin_hook" in deliverable.promo_bundle:
                promo_text += f"### LinkedIn Hook\n{deliverable.promo_bundle['linkedin_hook']}\n\n"
            if "tweet_thread" in deliverable.promo_bundle:
                promo_text += "### Tweet Thread\n"
                tweets = deliverable.promo_bundle.get("tweet_thread", [])
                for i, tweet in enumerate(tweets, 1):
                    promo_text += f"{i}. {tweet}\n"
                promo_text += "\n"
            if "newsletter_blurb" in deliverable.promo_bundle:
                promo_text += f"### Newsletter Blurb\n{deliverable.promo_bundle['newsletter_blurb']}\n\n"

        progress(1.0, desc="Complete!")

        # Format blog with title
        blog_markdown = f"# {deliverable.title}\n\n"
        blog_markdown += f"*{deliverable.meta_description}*\n\n"
        blog_markdown += "---\n\n"
        blog_markdown += deliverable.packaged_post

        return blog_markdown, quality_report, promo_text

    except Exception as e:
        import traceback
        error_msg = f"❌ Error: {str(e)}\n\n```\n{traceback.format_exc()}\n```"
        return error_msg, "", ""


# Create Gradio interface
with gr.Blocks(title="Blog Creation Agent", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🧭 Principal Engineer Blog Creation Agent
    
    Create high-quality technical blog posts with AI assistance.
    Provide either free-form input or structured fields below.
    """)

    with gr.Row():
        with gr.Column(scale=2):
            user_input = gr.Textbox(
                label="Free-form Input (Optional)",
                placeholder="e.g., I want to write about my experience with Kubernetes...",
                lines=3,
            )

            with gr.Row():
                persona = gr.Textbox(
                    label="Persona",
                    placeholder="e.g., Principal Software Engineer",
                )
                topic = gr.Textbox(
                    label="Topic",
                    placeholder="e.g., Microservices architecture patterns",
                )

            with gr.Row():
                goal = gr.Textbox(
                    label="Goal",
                    placeholder="e.g., Teach best practices",
                )
                voice = gr.Textbox(
                    label="Voice",
                    placeholder="e.g., Pragmatic mentor, data-backed",
                )

            create_btn = gr.Button("✨ Create Blog", variant="primary", size="lg")

        with gr.Column(scale=1):
            gr.Markdown("### 💡 Tips")
            gr.Markdown("""
            - **Free-form input**: Describe what you want to write about
            - **Structured fields**: Fill in specific details
            - **Both**: Free-form input takes priority if provided
            - The agent will create a complete blog with:
              - SEO optimization
              - Quality scoring
              - Promo materials
              - Visual storyboard
            """)

    with gr.Tabs():
        with gr.Tab("📝 Blog Post"):
            blog_output = gr.Markdown(label="Generated Blog")

        with gr.Tab("📊 Quality Report"):
            quality_output = gr.Markdown(label="Quality Metrics")

        with gr.Tab("📢 Promo Bundle"):
            promo_output = gr.Markdown(label="Promotional Content")

    # Connect button to function
    create_btn.click(
        fn=create_blog,
        inputs=[user_input, persona, topic, goal, voice],
        outputs=[blog_output, quality_output, promo_output],
    )

    # Example inputs
    gr.Examples(
        examples=[
            [
                "I want to write about my experience migrating from monoliths to microservices at my company",
                "",
                "",
                "",
                ""
            ],
            [
                "",
                "Principal Software Engineer",
                "Kubernetes best practices for production",
                "Teach practical deployment strategies",
                "Pragmatic mentor, data-backed"
            ],
            [
                "Write a blog about building scalable APIs using Python and FastAPI",
                "",
                "",
                "",
                ""
            ],
        ],
        inputs=[user_input, persona, topic, goal, voice],
    )


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
