"""
Enhanced YouTube workflow for 4-5 minute inspirational wisdom videos
with comprehensive agent prompts and review/enhancement cycles.
"""
from __future__ import annotations

import logging
import json
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from crewai import Agent, Task, Crew, Process
from langchain.tools import Tool

from src.ai_agentic_workflow.clients.chatgpt_client import DualModelChatClient
from src.ai_agentic_workflow.clients.gemini_client import DualModelGeminiClient
from src.ai_agentic_workflow.clients.claude_client import DualModelClaudeClient

logger = logging.getLogger(__name__)


@dataclass
class VideoProject:
    """Enhanced state object for wisdom video production."""
    initial_idea: str
    enhanced_concept: Optional[Dict[str, Any]] = None
    story_draft: Optional[str] = None
    story_review: Optional[Dict[str, Any]] = None
    enhanced_story: Optional[str] = None
    scene_breakdown: Optional[List[Dict[str, Any]]] = None
    script_review: Optional[Dict[str, Any]] = None
    enhanced_script: Optional[List[Dict[str, Any]]] = None
    visual_prompts: Optional[List[Dict[str, Any]]] = None
    audio_scripts: Optional[List[Dict[str, Any]]] = None
    quality_report: Optional[Dict[str, Any]] = None
    youtube_metadata: Optional[Dict[str, Any]] = None
    attempts: int = 0
    final_approved: bool = False


class YouTubeWisdomWorkflow:
    """Enhanced workflow for inspirational wisdom videos with review cycles."""

    def __init__(self):
        # Initialize clients according to prompt specifications
        self.gpt4_client = DualModelChatClient(
            reasoning_model="gpt-4",  # strong reasoning for reviews
            concept_model="gpt-3.5-turbo",  # cheaper for concept drafts
            default_model="reasoning",
        )

        self.claude_opus_client = DualModelClaudeClient(
            reasoning_model="claude-3-opus-20240229",
            concept_model="claude-3-sonnet-20240229",
            default_model="reasoning",
        )

        self.claude_sonnet_client = DualModelClaudeClient(
            reasoning_model="claude-3-sonnet-20240229",
            concept_model="claude-3-haiku-20240307",
            default_model="reasoning",
        )

        self.gemini_client = DualModelGeminiClient(
            reasoning_model="gemini-pro",  # Gemini 2.5 for creative writing
            concept_model="gemini-pro",
            default_model="reasoning",
        )

        self.gpt4_turbo_client = DualModelChatClient(
            reasoning_model="gpt-4-turbo-preview",
            concept_model="gpt-3.5-turbo",
            default_model="reasoning",
        )

        self.o3_mini_client = DualModelChatClient(
            reasoning_model="o3-mini",
            concept_model="gpt-3.5-turbo",
            default_model="reasoning",
        )

        # Define all 11 agents
        self._create_agents()

    def _create_agents(self):
        """Create all 11 agents with their detailed prompts."""

        # 1. Creative Director (GPT-4) - Concept Enhancement
        self.creative_director = Agent(
            role="Creative Director",
            goal="Enhance video concepts that combine ancient wisdom with modern life applications through engaging storytelling",
            backstory=(
                "You are a Creative Director specializing in inspirational and motivational content for YouTube. "
                "Your role is to enhance video concepts that teach life lessons through Buddhist tales, Zen stories, and wisdom parables "
                "for a general adult audience seeking personal growth. You focus on universal themes: inner peace, emotional control, "
                "relationships, success mindset, and overcoming adversity."
            ),
            llm=self.gpt4_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        # 2. Story Writer (Gemini) - Narrative Creation
        self.story_writer = Agent(
            role="Story Writer",
            goal="Create wisdom-based stories that teach profound life lessons through engaging storytelling",
            backstory=(
                "You are an expert story writer specializing in inspirational narratives for 4-5 minute videos "
                "targeting adults seeking personal growth and spiritual insights. You write 600-800 word stories using simple, "
                "profound, and conversational language with universal human struggles that viewers can relate to."
            ),
            llm=self.gemini_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        # 3. Story Reviewer (ChatGPT) - Story Quality Check
        self.story_reviewer = Agent(
            role="Story Reviewer",
            goal="Critically review wisdom stories for authenticity, emotional impact, and transformational value",
            backstory=(
                "You are a philosophical editor and story critic specializing in wisdom literature and inspirational content. "
                "You ensure stories maintain authenticity to wisdom traditions while being accessible to modern audiences. "
                "You evaluate narrative flow, emotional resonance, character development, and the clarity of the wisdom teaching."
            ),
            llm=self.gpt4_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        # 4. Story Enhancer (Claude Opus) - Story Improvement
        self.story_enhancer = Agent(
            role="Story Enhancer",
            goal="Refine and enhance wisdom stories based on review feedback to maximize inspirational impact",
            backstory=(
                "You are a master storyteller who specializes in taking good stories and making them exceptional. "
                "You incorporate feedback while maintaining the story's authentic voice and wisdom teaching. "
                "You enhance emotional moments, clarify wisdom teachings, and ensure the story flows perfectly for narration."
            ),
            llm=self.claude_opus_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        # 5. Script Writer (Gemini) - Scene Breakdown
        self.script_writer = Agent(
            role="Script Writer",
            goal="Transform wisdom stories into detailed scene-by-scene scripts optimized for 4-5 minute videos",
            backstory=(
                "You are a professional script writer specializing in inspirational video content. "
                "You break stories into 12-15 scenes with compelling openings and inspiring conclusions, writing in "
                "conversational, narrator-friendly language with timing cues and visual descriptions."
            ),
            llm=self.gemini_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        # 6. Script Reviewer (GPT-4 Turbo) - Script Quality Check
        self.script_reviewer = Agent(
            role="Script Reviewer",
            goal="Review scripts for pacing, visual storytelling, and emotional impact in video format",
            backstory=(
                "You are a video production expert who reviews scripts for flow, timing, and visual potential. "
                "You ensure each scene contributes to the narrative arc, maintains viewer engagement, and translates well to video. "
                "You check for proper pacing, clear narration, and effective scene transitions."
            ),
            llm=self.gpt4_turbo_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        # 7. Script Enhancer (Gemini) - Script Improvement
        self.script_enhancer = Agent(
            role="Script Enhancer",
            goal="Refine scripts based on review feedback for optimal video production",
            backstory=(
                "You are a script doctor who perfects video scripts for maximum impact. "
                "You enhance scene descriptions, improve narration flow, adjust timing, and ensure each scene "
                "builds toward the transformational message. You maintain the 4-5 minute format while maximizing engagement."
            ),
            llm=self.gemini_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        # 8. Visual Director (GPT-4 Turbo) - Image Generation Prompts
        self.visual_director = Agent(
            role="Visual Director",
            goal="Create detailed image generation prompts that convey deep philosophical concepts through engaging imagery",
            backstory=(
                "You are a Visual Director creating sophisticated, meaningful visual descriptions for "
                "inspirational videos targeting adults seeking wisdom and personal growth. You specialize in cinematic, "
                "contemplative illustrations with spiritual/philosophical depth."
            ),
            llm=self.gpt4_turbo_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        # 9. Sound Designer (Claude Sonnet) - Audio Script Creation
        self.sound_designer = Agent(
            role="Sound Designer",
            goal="Create comprehensive audio scripts that enhance the emotional and spiritual impact of wisdom-based storytelling",
            backstory=(
                "You are a Sound Designer specializing in inspirational video content for adults seeking "
                "wisdom and personal growth. You create contemplative, peaceful soundscapes with strategic use of silence "
                "and natural sounds that evoke peace and connection to nature."
            ),
            llm=self.claude_sonnet_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        # 10. Quality Controller (O3-mini) - Content Validation
        self.quality_controller = Agent(
            role="Quality Controller",
            goal="Ensure all content meets quality, authenticity, and impact standards for transformational video content",
            backstory=(
                "You are a Quality Controller specializing in inspirational and motivational content validation "
                "for adult audiences seeking wisdom and personal growth. You ensure content authenticity, inspirational value, "
                "cultural sensitivity, and emotional impact."
            ),
            llm=self.o3_mini_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

        # 11. Producer (GPT-4) - YouTube Optimization
        self.producer = Agent(
            role="Producer",
            goal="Optimize content for maximum reach, engagement, and positive impact in the personal development niche",
            backstory=(
                "You are a YouTube Producer specializing in inspirational and motivational content optimization "
                "for adult audiences seeking wisdom and personal transformation. You optimize for transformation promises, "
                "problem solutions, and wisdom authority."
            ),
            llm=self.gpt4_client.get_llm(),
            verbose=True,
            allow_delegation=False,
        )

    def _create_tasks(self, project: VideoProject) -> List[Task]:
        """Create all tasks with detailed prompts from specifications.

        If ``project.story_review`` is populated and ``project.attempts`` is
        greater than one, the story writing task incorporates the prior review
        feedback so the workflow can self-correct in subsequent attempts.
        """
        tasks: List[Task] = []

        # Task 1: Creative Director - Concept Enhancement
        enhance_task = Task(
            description=f"""
            You are enhancing this initial video idea: '{project.initial_idea}'

            Create an enhanced concept for a 4-5 minute YouTube video similar to \"Words of Wisdom Stories\" that teaches
            life lessons through Buddhist tales, Zen stories, and wisdom parables for a general adult audience seeking
            personal growth.

            CONCEPT ENHANCEMENT CRITERIA:
            1. Transformational Value: Offer genuine life-changing insights
            2. Relatability Factor: Address common human struggles and challenges
            3. Wisdom Integration: Seamlessly blend ancient teachings with modern applications
            4. Emotional Resonance: Create concepts that touch hearts and minds
            5. Practical Application: Ensure viewers can implement lessons in daily life
            6. Universal Appeal: Transcend cultural and religious boundaries

            VIDEO STRUCTURE FOR 4-5 MINUTES:
            - Opening Hook (30 seconds): Compelling question or scenario
            - Story Setup (45 seconds): Character introduction and situation
            - Core Narrative (2.5-3 minutes): Main story with wisdom teaching
            - Lesson Application (45-60 seconds): How to apply this wisdom today
            - Closing Inspiration (30 seconds): Motivational conclusion and call to reflection

            OUTPUT FORMAT as JSON:
            {{
                "enhanced_title": "transformation-focused title",
                "core_wisdom_teaching": "the main lesson",
                "target_life_challenge": "specific problem addressed",
                "story_framework": "Buddhist/Zen/Wisdom tale type",
                "modern_applications": ["example1", "example2"],
                "emotional_journey": "arc from struggle to transformation",
                "key_takeaway": "memorable closing message"
            }}
            IMPORTANT: Your entire response must be ONLY the JSON object, without any introductory text, comments, or markdown formatting like ```json.
            """,
            expected_output="Enhanced concept in JSON format",
            agent=self.creative_director,
        )
        tasks.append(enhance_task)

        # Task 2: Story Writer - Create Narrative
        improvement_block = ""
        if project.story_review and project.attempts > 1:
            improvement_block = (
                "\n\nPREVIOUS REVIEW FEEDBACK:\n"
                f"{json.dumps(project.story_review, indent=2)}\n"
                "Rewrite the story addressing these points."
            )

        story_task = Task(
            description=f"""
            Based on the enhanced concept from the Creative Director, write a complete wisdom-based story.

            STORY REQUIREMENTS:
            - Length: 600-800 words (suitable for 4-5 minute videos)
            - Language: Simple, profound, and conversational
            - Structure: Classical wisdom tale format with modern relevance
            - Characters: Archetypal figures (wise masters, seekers, kings, merchants, etc.)
            - Setting: Timeless environments that support the wisdom teaching

            STORYTELLING ELEMENTS TO INCLUDE:
            1. Universal human struggles that viewers can relate to
            2. Profound yet simple wisdom that transforms perspective
            3. Metaphorical elements that deepen understanding
            4. Emotional moments that create lasting impact
            5. Clear cause-and-effect relationships showing consequences of choices
            6. Practical wisdom that can be applied immediately

            STORY STRUCTURE TEMPLATE FOR 4-5 MINUTES:
            1. OPENING HOOK (30 seconds): Intriguing question or compelling scenario
            2. CHARACTER INTRODUCTION (45 seconds): Introduce protagonist facing a challenge
            3. CONFLICT DEVELOPMENT (60 seconds): Explore the struggle and its impact
            4. WISDOM ENCOUNTER (90-120 seconds): Meeting with wise figure or learning moment
            5. TRANSFORMATION (60 seconds): Character applies wisdom and experiences change
            6. RESOLUTION & LESSON (45 seconds): Clear outcome and wisdom teaching
            7. MODERN APPLICATION (30 seconds): How this applies to viewers' lives

            Write the complete narrative story following these guidelines.{improvement_block}
            """,
            expected_output="Complete 600-800 word narrative story",
            agent=self.story_writer,
            context=[enhance_task],
        )
        tasks.append(story_task)

        # Task 3: Story Reviewer - Review Story
        story_review_task = Task(
            description="""
            Review the wisdom story for quality, authenticity, and inspirational impact.

            REVIEW CRITERIA:
            1. **Wisdom Authenticity**: Is the wisdom teaching accurate and respectfully presented?
            2. **Emotional Journey**: Does the story create a compelling emotional arc?
            3. **Character Development**: Are characters relatable and their transformation believable?
            4. **Narrative Flow**: Does the story flow smoothly for narration?
            5. **Universal Appeal**: Will this resonate with a broad adult audience?
            6. **Practical Value**: Can viewers apply this wisdom in their lives?
            7. **Cultural Sensitivity**: Is the content respectful of all traditions?
            8. **Length & Pacing**: Is it appropriate for a 4-5 minute video?

            Provide specific feedback for improvement in each area.

            OUTPUT FORMAT as JSON:
            {{
                "overall_score": 0-100,
                "wisdom_authenticity": {{"score": 0-10, "feedback": "specific comments"}},
                "emotional_journey": {{"score": 0-10, "feedback": "specific comments"}},
                "character_development": {{"score": 0-10, "feedback": "specific comments"}},
                "narrative_flow": {{"score": 0-10, "feedback": "specific comments"}},
                "universal_appeal": {{"score": 0-10, "feedback": "specific comments"}},
                "practical_value": {{"score": 0-10, "feedback": "specific comments"}},
                "cultural_sensitivity": {{"score": 0-10, "feedback": "specific comments"}},
                "length_pacing": {{"score": 0-10, "feedback": "specific comments"}},
                "specific_improvements": ["improvement1", "improvement2"],
                "strong_points": ["strength1", "strength2"]
            }}
            IMPORTANT: Your entire response must be ONLY the JSON object, without any introductory text, comments, or markdown formatting like ```json.
            """,
            expected_output="Story review with scores and feedback in JSON format",
            agent=self.story_reviewer,
            context=[story_task],
        )
        tasks.append(story_review_task)

        # Task 4: Story Enhancer - Enhance Story
        story_enhance_task = Task(
            description="""
            Enhance the wisdom story based on the reviewer's feedback while maintaining its authentic voice.

            You have:
            1. The original story
            2. Detailed review feedback with specific improvement suggestions

            ENHANCEMENT GUIDELINES:
            - Address all specific improvements mentioned in the review
            - Strengthen areas with lower scores
            - Maintain the story's core wisdom teaching and emotional arc
            - Keep the 600-800 word length for 4-5 minute narration
            - Enhance but don't completely rewrite - preserve what works well
            - Ensure smooth, conversational flow for narration
            - Deepen emotional moments where suggested
            - Clarify wisdom teachings if needed
            - Improve character relatability

            Write the enhanced version of the story incorporating all feedback.
            """,
            expected_output="Enhanced 600-800 word narrative story",
            agent=self.story_enhancer,
            context=[story_task, story_review_task],
        )
        tasks.append(story_enhance_task)

        # Task 5: Script Writer - Scene Breakdown
        script_improvement_block = ""
        if project.script_review and project.attempts > 1:
            script_improvement_block = (
                "\n\nPREVIOUS SCRIPT REVIEW FEEDBACK:\n"
                f"{json.dumps(project.script_review, indent=2)}\n"
                "Rewrite the script addressing these points."
            )

        script_task = Task(
            description=f"""
            Transform the enhanced wisdom story into a detailed scene-by-scene script optimized for a 4-5 minute video.

            SCRIPT CONVERSION GUIDELINES:
            - Break stories into 12-15 scenes for 4-5 minute videos
            - Include 30-second opening hook and 30-second closing inspiration
            - Write in conversational, narrator-friendly language
            - Add timing cues for pacing and emphasis
            - Include background music and sound effect cues
            - Specify visual descriptions for each scene

            SCENE STRUCTURE FORMAT:
            **SCENE [NUMBER]: [TITLE]**
            - **Duration:** [X seconds]
            - **Visual:** [Detailed scene description for animation/illustration]
            - **Narration:** [Exact words for voice-over]
            - **Music:** [Background music mood and timing]
            - **Sound Effects:** [Specific audio enhancements]
            - **Emphasis:** [Words or phrases to stress]
            - **Transition:** [How scene flows to next]

            OUTPUT FORMAT as JSON:
            {{
                "total_duration_seconds": calculated total,
                "scenes": [
                    {{
                        "scene_number": 1,
                        "title": "scene title",
                        "duration_seconds": 30,
                        "visual_description": "what viewers see",
                        "narration": "exact narrator text",
                        "music": "background music description",
                        "sound_effects": ["effect1", "effect2"],
                        "emphasis_words": ["key", "words"],
                        "transition": "fade/cut/etc"
                    }}
                ]
            }}
            {script_improvement_block}
            IMPORTANT: Your entire response must be ONLY the JSON object, without any introductory text, comments, or markdown formatting like ```json.
            """,
            expected_output="Scene breakdown in JSON format",
            agent=self.script_writer,
            context=[story_enhance_task],
        )
        tasks.append(script_task)

        # Task 6: Script Reviewer - Review Script
        script_review_task = Task(
            description="""
            Review the video script for production quality, pacing, and viewer engagement.

            SCRIPT REVIEW CRITERIA:
            1. **Opening Hook**: Does it grab attention in the first 15 seconds?
            2. **Scene Flow**: Do scenes transition smoothly?
            3. **Visual Potential**: Can each scene be effectively visualized?
            4. **Narration Quality**: Is the language natural and engaging?
            5. **Pacing**: Does timing work for a 4-5 minute video?
            6. **Emotional Beats**: Are key emotional moments properly emphasized?
            7. **Sound Design**: Are audio cues appropriate and effective?
            8. **Closing Impact**: Does it end with inspiration and a clear takeaway?

            OUTPUT FORMAT as JSON:
            {{
                "overall_score": 0-100,
                "opening_hook": {{"score": 0-10, "feedback": "specific comments"}},
                "scene_flow": {{"score": 0-10, "feedback": "specific comments"}},
                "visual_potential": {{"score": 0-10, "feedback": "specific comments"}},
                "narration_quality": {{"score": 0-10, "feedback": "specific comments"}},
                "pacing": {{"score": 0-10, "feedback": "specific comments"}},
                "emotional_beats": {{"score": 0-10, "feedback": "specific comments"}},
                "sound_design": {{"score": 0-10, "feedback": "specific comments"}},
                "closing_impact": {{"score": 0-10, "feedback": "specific comments"}},
                "scene_specific_feedback": {{"scene_X": "feedback"}},
                "improvement_suggestions": ["suggestion1", "suggestion2"]
            }}
            IMPORTANT: Your entire response must be ONLY the JSON object, without any introductory text, comments, or markdown formatting like ```json.
            """,
            expected_output="Script review with detailed feedback in JSON format",
            agent=self.script_reviewer,
            context=[script_task],
        )
        tasks.append(script_review_task)

        # Task 7: Script Enhancer - Enhance Script
        script_enhance_task = Task(
            description="""
            Enhance the video script based on reviewer feedback for optimal production value.

            ENHANCEMENT FOCUS:
            - Strengthen the opening hook if needed
            - Improve scene transitions
            - Enhance visual descriptions
            - Refine narration for natural flow
            - Adjust timing for perfect pacing
            - Amplify emotional moments
            - Optimize sound design cues
            - Strengthen the closing impact

            Maintain the 4-5 minute total duration while incorporating all improvements.

            OUTPUT FORMAT: Same JSON structure as the original script with all enhancements applied.
            IMPORTANT: Your entire response must be ONLY the JSON object, without any introductory text, comments, or markdown formatting like ```json.
            """,
            expected_output="Enhanced scene breakdown in JSON format",
            agent=self.script_enhancer,
            context=[script_task, script_review_task],
        )
        tasks.append(script_enhance_task)

        # Task 8: Visual Director - Image Prompts
        # Executed asynchronously alongside Task 9
        visual_task = Task(
            description="""
            Create detailed image generation prompts for each scene in the enhanced script.

            VISUAL STYLE REQUIREMENTS:
            - Art style: Cinematic, contemplative illustrations with spiritual/philosophical depth
            - Color palette: Warm, earthy tones with strategic use of golden light and deep blues
            - Character design: Archetypal figures representing wisdom, seeking, and transformation
            - Environment: Serene, timeless settings that evoke peace and contemplation
            - Composition: Symbolic imagery that supports the wisdom teaching

            For each scene, create prompts following this structure:
            {{
                "scene_number": X,
                "main_subject": "character or symbolic element with emotional state",
                "setting": "environment that supports the wisdom theme",
                "lighting": "mood lighting description",
                "color_palette": "specific colors",
                "symbolic_elements": ["element1", "element2"],
                "composition": "camera angle and framing",
                "mood": "overall feeling",
                "style_modifiers": ["cinematic", "contemplative", "spiritual"],
                "aspect_ratio": "16:9",
            }}

            OUTPUT FORMAT as JSON:
            {{
                "visual_prompts": [array of prompt objects for each scene]
            }}
            IMPORTANT: Your entire response must be ONLY the JSON object, without any introductory text, comments, or markdown formatting like ```json.
            """,
            expected_output="Visual prompts in JSON format",
            agent=self.visual_director,
            context=[script_enhance_task],
            async_execution=True,
        )
        tasks.append(visual_task)

        # Task 9: Sound Designer - Audio Scripts
        # Runs in parallel with Task 8
        audio_task = Task(
            description="""
            Create comprehensive audio scripts for the enhanced video scenes.

            AUDIO DESIGN PRINCIPLES:
            - Contemplative, peaceful soundscapes that support reflection
            - Subtle, non-intrusive background music that enhances without competing
            - Strategic use of silence for powerful moments
            - Natural sounds that evoke peace and connection to nature

            VOICE DIRECTION FOR NARRATION:
            - Tone: Warm, conversational, wise but approachable
            - Pace: Slower than conversational speech, allowing for absorption
            - Emphasis: Gentle stress on key wisdom points without being preachy
            - Emotion: Convey genuine care and understanding for human struggles
            - Pauses: Strategic silence for reflection and emotional impact

            For each scene, specify:
            {{
                "scene_number": X,
                "narration_direction": {{
                    "tone": "emotional quality",
                    "pace": "speed guidance",
                    "emphasis_points": ["key phrases"],
                    "pause_locations": ["after X", "before Y"]
                }},
                "background_music": {{
                    "style": "musical style",
                    "intensity": "low/medium",
                    "instruments": ["piano", "strings"]
                }},
                "ambient_sounds": ["nature sounds", "environmental audio"],
                "silence_moments": ["strategic pauses"]
            }}

            OUTPUT FORMAT as JSON:
            {{
                "audio_scripts": [array of audio direction objects for each scene]
            }}
            IMPORTANT: Your entire response must be ONLY the JSON object, without any introductory text, comments, or markdown formatting like ```json.
            """,
            expected_output="Audio scripts in JSON format",
            agent=self.sound_designer,
            context=[script_enhance_task],
            async_execution=True,
        )
        tasks.append(audio_task)

        # Task 10: Quality Control - Validation
        quality_task = Task(
            description="""
            Validate all content for quality, authenticity, and transformational impact.

            VALIDATION CHECKLIST:
            1. Content Authenticity & Wisdom Accuracy
            2. Inspirational Value Assessment
            3. Cultural & Spiritual Sensitivity
            4. Emotional Impact Verification
            5. Technical Quality Standards
            6. Message Clarity & Practical Application
            7. Platform Optimization & Engagement

            Review all previous outputs and provide:

            OUTPUT FORMAT as JSON:
            {{
                "approval_status": "APPROVED/NEEDS_REVISION",
                "authenticity_check": {{"status": "PASS/FAIL", "notes": "details"}},
                "inspirational_value": {{"status": "PASS/FAIL", "notes": "details"}},
                "cultural_sensitivity": {{"status": "PASS/FAIL", "notes": "details"}},
                "emotional_impact": {{"status": "PASS/FAIL", "notes": "details"}},
                "technical_quality": {{"status": "PASS/FAIL", "notes": "details"}},
                "message_clarity": {{"status": "PASS/FAIL", "notes": "details"}},
                "revision_recommendations": ["specific improvements needed"],
                "quality_score": 0-100
            }}
            IMPORTANT: Your entire response must be ONLY the JSON object, without any introductory text, comments, or markdown formatting like ```json.
            """,
            expected_output="Quality validation report in JSON format",
            agent=self.quality_controller,
            context=[story_enhance_task, script_enhance_task, visual_task, audio_task],
        )
        tasks.append(quality_task)

        # Task 11: Producer - YouTube Optimization
        youtube_task = Task(
            description="""
            Create optimized YouTube metadata for maximum reach and engagement.
            Before generating metadata, check the Quality Controller's report. If approval_status is "NEEDS_REVISION", return placeholder metadata and highlight required fixes.

            OPTIMIZATION REQUIREMENTS:
            - Title: Transformation promise with wisdom authority (50-70 characters)
            - Description: Hook, value proposition, transformation promise
            - Tags: Mix of high, medium, and low competition keywords
            - Thumbnail: Compelling imagery with 2-4 power words

            TITLE TEMPLATES:
            - "This [Ancient Wisdom] Will Transform How You [Life Area] | [Story Type]"
            - "You'll Never [Negative Behavior] Again After This [Wisdom Source] Story"
            - "The [Character] Who [Action] | Life-Changing Lesson About [Theme]"

            OUTPUT FORMAT as JSON:
            {{
                "title_options": ["title1", "title2", "title3"],
                "description": "full YouTube description with timestamps",
                "tags": ["tag1", "tag2"],
                "thumbnail_concept": {{
                    "visual_elements": "description",
                    "text_overlay": "2-4 power words",
                    "color_scheme": "colors that grab attention"
                }},
                "publishing_schedule": {{
                    "best_time": "day and time",
                    "frequency": "posting schedule"
                }},
                "engagement_strategy": "community interaction plan"
            }}
            IMPORTANT: Your entire response must be ONLY the JSON object, without any introductory text, comments, or markdown formatting like ```json.
            """,
            expected_output="YouTube optimization package in JSON format",
            agent=self.producer,
            context=[enhance_task, story_enhance_task, quality_task],
        )
        tasks.append(youtube_task)

        return tasks

    STORY_REVIEW_THRESHOLD = 85
    MAX_RETRIES = 3
    SCRIPT_REVIEW_THRESHOLD = 85

    def run(self, initial_idea: str, debug: bool = False) -> VideoProject:
        """Run the complete workflow for wisdom video generation with self-correction.

        Parameters
        ----------
        initial_idea: str
            The raw idea for the video.
        debug: bool, optional
            When ``True`` the workflow emits verbose logs of all agent
            invocations and parsed outputs.

        Notes
        -----
        The Visual Director and Sound Designer steps execute asynchronously
        to reduce runtime while the script remains sequential elsewhere. If the
        story review score falls below ``STORY_REVIEW_THRESHOLD`` the entire
        pipeline automatically retries with the reviewer feedback incorporated.
        """
        project = VideoProject(initial_idea=initial_idea)

        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug logging enabled")

        for attempt in range(1, self.MAX_RETRIES + 1):
            project.attempts = attempt
            logger.info("Starting workflow attempt %s", attempt)

            tasks = self._create_tasks(project)
            crew = Crew(
                agents=[
                    self.creative_director,
                    self.story_writer,
                    self.story_reviewer,
                    self.story_enhancer,
                    self.script_writer,
                    self.script_reviewer,
                    self.script_enhancer,
                    self.visual_director,
                    self.sound_designer,
                    self.quality_controller,
                    self.producer,
                ],
                tasks=tasks,
                process=Process.sequential,
                verbose=debug,
                memory=True,
                cache=True,
            )

            result = crew.kickoff()

            try:
                task_outputs = result.tasks_output
                project.enhanced_concept = self._parse_json_output(task_outputs[0].raw)
                logger.debug("Enhanced concept: %s", project.enhanced_concept)
                project.story_draft = task_outputs[1].raw
                logger.debug("Story draft: %s", project.story_draft)
                project.story_review = self._parse_json_output(task_outputs[2].raw)
                logger.debug("Story review: %s", project.story_review)
                project.enhanced_story = task_outputs[3].raw
                logger.debug("Enhanced story: %s", project.enhanced_story)
                project.scene_breakdown = self._parse_json_output(task_outputs[4].raw).get("scenes", [])
                logger.debug("Scene breakdown: %s", project.scene_breakdown)
                project.script_review = self._parse_json_output(task_outputs[5].raw)
                logger.debug("Script review: %s", project.script_review)
                project.enhanced_script = self._parse_json_output(task_outputs[6].raw).get("scenes", [])
                logger.debug("Enhanced script: %s", project.enhanced_script)
                project.visual_prompts = self._parse_json_output(task_outputs[7].raw).get("visual_prompts", [])
                logger.debug("Visual prompts: %s", project.visual_prompts)
                project.audio_scripts = self._parse_json_output(task_outputs[8].raw).get("audio_scripts", [])
                logger.debug("Audio scripts: %s", project.audio_scripts)
                project.quality_report = self._parse_json_output(task_outputs[9].raw)
                logger.debug("Quality report: %s", project.quality_report)
                project.youtube_metadata = self._parse_json_output(task_outputs[10].raw)
                logger.debug("YouTube metadata: %s", project.youtube_metadata)

                if project.quality_report.get("approval_status") == "APPROVED":
                    project.final_approved = True
                else:
                    logger.warning(
                        "Quality control failed with status: %s",
                        project.quality_report.get("approval_status"),
                    )
                    project.youtube_metadata = {}

                score = project.story_review.get("overall_score", 0)
                script_score = project.script_review.get("overall_score", 0)
                logger.info("Story review score: %s", score)
                logger.info("Script review score: %s", script_score)
                if (score >= self.STORY_REVIEW_THRESHOLD and script_score >= self.SCRIPT_REVIEW_THRESHOLD) or attempt == self.MAX_RETRIES:
                    break
                logger.info(
                    "Scores below threshold (story %s/<%s>, script %s/<%s>), retrying...",
                    score,
                    self.STORY_REVIEW_THRESHOLD,
                    script_score,
                    self.SCRIPT_REVIEW_THRESHOLD,
                )
            except Exception as e:
                logger.error(f"Error processing crew outputs: {e}")
                break

        return project

    def _parse_json_output(self, raw_output: str) -> Dict[str, Any]:
        """Parse JSON from agent output."""
        try:
            json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            logger.warning("No JSON found in output")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {}


def run_youtube_wisdom_workflow(initial_idea: str, debug: bool = False) -> Dict[str, Any]:
    """Convenience wrapper to run the workflow and return results.

    Parameters
    ----------
    initial_idea : str
        Raw seed idea for the video.
    debug : bool, optional
        If ``True`` enables verbose logging of all agent interactions.

    Notes
    -----
    Visual and audio generation run concurrently within the workflow. The story
    phase automatically retries if the initial draft receives a low review
    score.
    """
    workflow = YouTubeWisdomWorkflow()
    project = workflow.run(initial_idea, debug=debug)
    return {
        "initial_idea": project.initial_idea,
        "enhanced_concept": project.enhanced_concept,
        "story_draft": project.story_draft,
        "story_review": project.story_review,
        "enhanced_story": project.enhanced_story,
        "scene_breakdown": project.scene_breakdown,
        "script_review": project.script_review,
        "enhanced_script": project.enhanced_script,
        "visual_prompts": project.visual_prompts,
        "audio_scripts": project.audio_scripts,
        "quality_report": project.quality_report,
        "youtube_metadata": project.youtube_metadata,
        "final_approved": project.final_approved,
        "attempts": project.attempts,
    }


if __name__ == "__main__":
    debug_mode = True
    logging.basicConfig(level=logging.DEBUG if debug_mode else logging.INFO)

    ideas = [
        "A monk who waited 10 years to ask one question",
        "The merchant who gave away his fortune to find peace",
        "A student learns the true meaning of patience through a butterfly",
        "The wise woman who taught happiness through an empty cup",
    ]

    result = run_youtube_wisdom_workflow(ideas[0], debug=debug_mode)

    print("\n=== WORKFLOW RESULTS ===")
    print(f"Story Title: {result['enhanced_concept'].get('enhanced_title', 'N/A')}")
    print(f"Story Review Score: {result['story_review'].get('overall_score', 'N/A')}/100")
    print(f"Script Review Score: {result['script_review'].get('overall_score', 'N/A')}/100")
    print(f"Final Quality Score: {result['quality_report'].get('quality_score', 'N/A')}/100")
    print(f"Approved: {result['final_approved']}")
    print("\nYouTube Title Options:")
    for title in result['youtube_metadata'].get('title_options', []):
        print(f"  - {title}")
