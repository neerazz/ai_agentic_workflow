# Persona Setup Guide for Neeraj Kumar Singh

## Quick Start

Run this command to fetch your LinkedIn data and establish your persona:

```bash
python setup_user_persona.py
```

This will:
1. ✅ Fetch your LinkedIn profile and all posts from: https://www.linkedin.com/in/neerajkumarsinghb/
2. ✅ Extract comprehensive persona information
3. ✅ Save persona memory to `neeraj_persona_memory.json`
4. ✅ Establish it as the default persona for all future blog creations

## What Gets Extracted

### From Your LinkedIn Profile
- **Role & Experience**: Current role, years of experience
- **Technical Skills**: All technologies with years of experience
- **Career Highlights**: Major achievements and milestones
- **Project Experiences**: Notable projects with descriptions
- **Education & Certifications**

### From Your LinkedIn Posts
- **Writing Voice**: Your unique writing style and tone
- **Common Phrases**: Frequently used expressions
- **Storytelling Patterns**: How you structure stories
- **Content Preferences**: Topics you frequently write about
- **Engagement Style**: How you connect with your audience
- **Brand Values**: Core values and principles you express

### Generated Summaries
- **Voice Summary**: 2-3 sentence summary of your writing voice
- **Expertise Summary**: 2-3 sentence summary of your technical expertise
- **Story Bank Summary**: Available stories and experiences for blog content

## After Setup

Once persona is established, you can create blogs in two ways:

### Option 1: Automatic (Recommended)
```bash
# System automatically uses your established persona
python examples/blog_creation_agent_cli_enhanced.py \
  --topic "Kubernetes best practices"
```

### Option 2: Explicit
```bash
# Explicitly specify persona memory file
python examples/blog_creation_agent_cli_enhanced.py \
  --topic "Microservices architecture" \
  --persona-memory neeraj_persona_memory.json
```

## Refreshing Your Persona

When you have new LinkedIn posts, refresh your persona:

```bash
python setup_user_persona.py
```

This will:
- Fetch your latest posts
- Update persona with new information
- Keep existing experience data

## Files Created

After running setup:

```
neeraj_persona_memory.json    # Your extracted persona (reusable)
persona_config.json           # Default persona configuration
.linkedin_cache/              # Cached LinkedIn data
  ├── cache_metadata.json
  ├── neerajkumarsinghb_posts.txt
  ├── neerajkumarsinghb_profile.txt
  └── neerajkumarsinghb_resume.txt
```

## Requirements

Make sure you have:
- `PERPLEXITY_API_KEY` set in environment or `.env` file
- Required Python packages installed (`pip install -r requirements.txt`)

## Troubleshooting

### No Data Fetched
- Check `PERPLEXITY_API_KEY` is set correctly
- Verify your LinkedIn profile is public or accessible
- Check Perplexity API quota

### Persona Extraction Fails
- Ensure LinkedIn data was fetched successfully
- Check logs for specific errors
- Try running setup again

### Cache Issues
- Delete `.linkedin_cache/` directory to start fresh
- Run setup again to re-fetch data

## Your Established Persona

Once setup is complete, your persona will be used automatically for:
- ✅ Voice and style matching in blog posts
- ✅ Authentic experience alignment
- ✅ Story selection from your career highlights
- ✅ Technical expertise references
- ✅ Brand values and mentorship style
- ✅ Common phrases and storytelling patterns

All future blog creations will automatically reflect your authentic voice and experience!
