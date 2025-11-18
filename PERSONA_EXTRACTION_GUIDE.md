# Persona Extraction and Memory System

## Overview

The Blog Creation Agent now includes an efficient **Persona Extraction and Memory System** that processes LinkedIn posts, profile, and resume data to create a compact, reusable persona representation. This avoids dumping all LinkedIn data into every prompt, making the system more efficient and cost-effective.

## Key Features

### ✅ Efficient Memory Storage
- **PersonaMemory**: Compact data structure storing extracted persona information
- **Smart Sampling**: Only uses most recent/relevant posts (last 10)
- **Text Truncation**: Limits text samples to avoid token bloat (500-2000 chars per source)
- **Compact Summaries**: Creates 2-3 sentence summaries for voice, expertise, and stories

### ✅ Reusable Across Stages
- Persona memory is extracted once and reused throughout all 16 stages
- Each stage references compact persona data, not raw LinkedIn content
- Reduces context window usage by 80-90%

### ✅ Multi-Source Support
- LinkedIn Posts (analyzes writing voice and style)
- LinkedIn Profile (extracts technical expertise and career highlights)
- Resume (optional, additional context)

## How It Works

### 1. Persona Extraction Process

```
LinkedIn Data → PersonaExtractor → PersonaMemory → Reused in All Stages
```

**Extraction Steps:**
1. **Core Identity**: Role, expertise areas, years of experience
2. **Voice & Style**: Writing patterns, common phrases, tone markers
3. **Technical Expertise**: Skills, career highlights, projects
4. **Content Preferences**: Topics, engagement patterns
5. **Brand Values**: Pillars, values, mentorship style
6. **Compact Summaries**: Voice, expertise, and story bank summaries

### 2. Memory Storage Structure

```python
PersonaMemory(
    # Core (compact)
    role: str
    expertise_areas: List[str]
    voice_summary: str  # 2-3 sentences
    expertise_summary: str  # 2-3 sentences
    story_bank_summary: str  # 2-3 sentences
    
    # Detailed (used when needed)
    technical_skills: Dict[str, int]
    career_highlights: List[Dict]
    common_phrases: List[str]
    storytelling_patterns: List[str]
    # ... more
)
```

### 3. Usage in Blog Creation

**Before (Inefficient):**
```python
# Every prompt includes ALL LinkedIn data
prompt = f"""
Write blog post.
LinkedIn Posts: {all_posts}  # Could be 10,000+ tokens
LinkedIn Profile: {full_profile}  # Could be 5,000+ tokens
Topic: {topic}
"""
```

**After (Efficient):**
```python
# Extract once, reuse compact data
persona_memory = extract_persona(posts, profile)
# Later stages use compact summaries
prompt = f"""
Write blog post.
Voice Summary: {persona_memory.voice_summary}  # ~50 tokens
Expertise: {persona_memory.expertise_summary}  # ~50 tokens
Available Stories: {persona_memory.story_bank_summary}  # ~50 tokens
Topic: {topic}
"""
```

## Usage Examples

### Example 1: Extract Persona First, Then Create Blog

```python
from src.ai_agentic_workflow.agents import BlogCreationAgent, PersonaExtractor

# Initialize
agent = BlogCreationAgent(config=get_free_tier_blog_config())
persona_extractor = PersonaExtractor()

# Extract persona
persona_result = persona_extractor.execute("", context={
    "linkedin_posts": your_linkedin_posts,
    "linkedin_profile": your_linkedin_profile,
    "resume": your_resume,  # Optional
})

if persona_result.success:
    persona_memory = persona_result.output
    
    # Save for reuse
    persona_memory.save("my_persona.json")
    
    # Create blog using persona
    result = agent.execute(
        "Write about microservices",
        context={"persona_memory": persona_memory}
    )
```

### Example 2: Extract and Create in One Call

```python
# Agent automatically extracts persona if LinkedIn data provided
result = agent.execute(
    "Write about Kubernetes",
    context={
        "linkedin_posts": your_posts,
        "linkedin_profile": your_profile,
    }
)
```

### Example 3: Load Saved Persona

```python
from src.ai_agentic_workflow.agents import PersonaMemory

# Load previously extracted persona
persona = PersonaMemory.load("my_persona.json")

# Use for multiple blogs
result1 = agent.execute("Topic 1", context={"persona_memory": persona})
result2 = agent.execute("Topic 2", context={"persona_memory": persona})
```

## What Gets Extracted

### From LinkedIn Posts
- **Writing Style**: Conversational, technical, storytelling patterns
- **Common Phrases**: Frequently used expressions
- **Tone Markers**: Words/phrases indicating tone
- **Storytelling Patterns**: How stories are structured
- **Content Preferences**: Topics frequently written about
- **Engagement Style**: How author connects with audience

### From LinkedIn Profile/Resume
- **Core Identity**: Role, expertise areas, years of experience
- **Technical Skills**: Technologies with years of experience
- **Career Highlights**: Major achievements
- **Project Experiences**: Notable projects with descriptions
- **Brand Values**: Core values and brand pillars
- **Mentorship Style**: How author mentors/teaches

## Efficiency Gains

### Token Usage Comparison

**Without Persona Memory:**
- Each stage: ~15,000-20,000 tokens (all LinkedIn data)
- 16 stages: ~240,000-320,000 tokens total

**With Persona Memory:**
- Extraction: ~5,000 tokens (one-time)
- Each stage: ~2,000-3,000 tokens (compact summaries)
- 16 stages: ~32,000-48,000 tokens + 5,000 extraction = ~37,000-53,000 tokens

**Savings: ~85% reduction in token usage**

### Cost Savings
- 85% fewer tokens = 85% lower API costs
- Faster execution (smaller prompts = faster responses)
- Better quality (LLMs perform better with focused context)

## Integration with Blog Creation Stages

The persona memory is used efficiently across all stages:

1. **PersonaArchitect**: Uses `voice_summary`, `brand_pillars`, `mentorship_style`
2. **ExperienceAligner**: Uses `career_highlights`, `project_experiences`, `story_bank_summary`
3. **DraftCrafter**: Uses `voice_summary`, `common_phrases`, `storytelling_patterns`
4. **VoiceGuardian**: Uses `voice_summary`, `tone_markers`
5. **CritiqueCouncil**: Uses `voice_summary`, `common_phrases`, `brand_pillars`

Each stage only includes the relevant compact data, not the full LinkedIn content.

## Best Practices

1. **Extract Once, Reuse Many**: Extract persona once and reuse for multiple blogs
2. **Save Persona Memory**: Use `persona_memory.save()` to persist for future use
3. **Update Periodically**: Re-extract persona when you have new LinkedIn posts
4. **Use Latest Posts**: System automatically uses most recent posts (last 10)
5. **Include Resume**: Resume provides additional context for technical expertise

## File Structure

```
persona_memory.json  # Saved persona data
{
  "role": "Principal Software Engineer",
  "expertise_areas": ["Microservices", "Kubernetes", ...],
  "voice_summary": "Pragmatic mentor who shares...",
  "expertise_summary": "14 years of experience...",
  "story_bank_summary": "Experiences include...",
  "technical_skills": {"Python": 8, "Kubernetes": 5, ...},
  "career_highlights": [...],
  ...
}
```

## Troubleshooting

### Persona Extraction Fails
- Check that LinkedIn data is provided (posts or profile)
- Ensure API keys are set (GOOGLE_API_KEY, GROQ_API_KEY)
- Check logs for specific error messages

### Persona Not Used in Blog Creation
- Verify persona_memory is in context: `context={"persona_memory": persona}`
- Check agent logs to confirm persona extraction succeeded
- Ensure persona_memory is not None before blog creation

### Low Quality Persona Data
- Provide more LinkedIn posts (at least 5-10 recent posts)
- Include detailed LinkedIn profile with work experience
- Add resume for additional technical context

## Summary

The Persona Extraction and Memory System provides:
- ✅ **85% reduction** in token usage
- ✅ **Reusable persona** across multiple blogs
- ✅ **Efficient context** management
- ✅ **Better quality** with focused persona data
- ✅ **Cost savings** from reduced API calls
- ✅ **Persistent storage** for persona data

This makes the blog creation agent much more efficient and cost-effective while maintaining high quality output that matches your authentic voice and experience.
