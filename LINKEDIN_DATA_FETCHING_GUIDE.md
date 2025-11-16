# LinkedIn Data Fetching and Caching Guide

## Overview

The Blog Creation Agent now includes automatic LinkedIn data fetching using Perplexity AI for web search. Data is automatically cached locally, so you only need to fetch once and it's reused for all future blog creations.

## Key Features

### ✅ Automatic Fetching
- Provide LinkedIn profile URL → Automatically fetches profile and posts
- Uses Perplexity AI for web search (no manual scraping needed)
- Fetches profile, posts, and resume data

### ✅ Smart Caching
- Data is cached locally in `.linkedin_cache/` directory
- Automatically uses cached data if available
- Only fetches when needed (first time or when refreshed)

### ✅ Seamless Integration
- If no URL provided, automatically uses most recent cached data
- Works with file-based input (backward compatible)
- Supports refresh options for updating posts

## Usage

### Basic Usage - First Time

```bash
# Provide LinkedIn URL - fetches and caches automatically
python examples/blog_creation_agent_cli_enhanced.py \
  --topic "Kubernetes best practices" \
  --linkedin-url "https://www.linkedin.com/in/yourprofile"
```

**What happens:**
1. Fetches LinkedIn profile using Perplexity
2. Fetches recent posts (last 20)
3. Attempts to fetch resume data
4. Saves all data to `.linkedin_cache/` directory
5. Uses the data for persona extraction and blog creation

### Subsequent Usage - Automatic Cache

```bash
# No URL needed - automatically uses cached data
python examples/blog_creation_agent_cli_enhanced.py \
  --topic "Microservices architecture"
```

**What happens:**
1. Checks for cached LinkedIn data
2. Uses most recently cached profile automatically
3. No API calls needed (unless you want to refresh)

### Refresh Posts Only

```bash
# Refresh posts but keep cached profile
python examples/blog_creation_agent_cli_enhanced.py \
  --topic "Docker containerization" \
  --linkedin-url "https://www.linkedin.com/in/yourprofile" \
  --refresh-posts
```

### Refresh Everything

```bash
# Force refresh all data
python examples/blog_creation_agent_cli_enhanced.py \
  --topic "System design" \
  --linkedin-url "https://www.linkedin.com/in/yourprofile" \
  --refresh-all
```

## Cache Structure

```
.linkedin_cache/
├── cache_metadata.json          # Cache metadata (URLs, timestamps)
├── username_posts.txt           # Cached posts (JSON format)
├── username_profile.txt         # Cached profile
└── username_resume.txt          # Cached resume (if available)
```

### Cache Metadata

The `cache_metadata.json` file tracks:
- Profile URLs that have been fetched
- Last fetch timestamp
- File locations for cached data
- Fetch count

## Workflow

### First Time Setup

```
1. User provides LinkedIn URL
   ↓
2. LinkedInDataFetcher fetches data via Perplexity
   ↓
3. Data saved to .linkedin_cache/
   ↓
4. Persona extracted from data
   ↓
5. Blog created using persona
```

### Subsequent Runs

```
1. User runs script (no URL)
   ↓
2. System checks cache
   ↓
3. Uses cached data automatically
   ↓
4. Persona extracted (or loaded from saved persona)
   ↓
5. Blog created
```

## Command Line Options

### LinkedIn Data Options

```bash
--linkedin-url URL           # LinkedIn profile URL (fetches automatically)
--linkedin-posts FILE       # Path to posts file (manual input)
--linkedin-profile FILE     # Path to profile file (manual input)
--resume FILE               # Path to resume file (manual input)
--refresh-posts             # Refresh posts only
--refresh-all               # Force refresh all data
--cache-dir DIR             # Custom cache directory (default: .linkedin_cache)
```

### Examples

```bash
# Fetch from URL (first time)
python examples/blog_creation_agent_cli_enhanced.py \
  --topic "Kubernetes" \
  --linkedin-url "https://www.linkedin.com/in/johndoe"

# Use cached data (automatic)
python examples/blog_creation_agent_cli_enhanced.py \
  --topic "Docker"

# Refresh posts only
python examples/blog_creation_agent_cli_enhanced.py \
  --topic "Microservices" \
  --linkedin-url "https://www.linkedin.com/in/johndoe" \
  --refresh-posts

# Use files instead of URL
python examples/blog_creation_agent_cli_enhanced.py \
  --topic "System Design" \
  --linkedin-posts posts.txt \
  --linkedin-profile profile.txt
```

## How It Works

### 1. URL-Based Fetching

When you provide `--linkedin-url`:
- Uses Perplexity AI to search and extract LinkedIn data
- Fetches comprehensive profile information
- Extracts recent posts (up to 20)
- Attempts to extract resume-style information
- Saves everything to cache

### 2. Cache Lookup

When no URL is provided:
- Checks `.linkedin_cache/` directory
- Finds most recently cached profile
- Loads cached data automatically
- No API calls needed

### 3. File-Based Input (Backward Compatible)

You can still provide files directly:
- `--linkedin-posts`: Posts file (JSON array or one per line)
- `--linkedin-profile`: Profile text file
- `--resume`: Resume text file

## API Requirements

### Perplexity API Key

For URL-based fetching, you need:
```bash
export PERPLEXITY_API_KEY="your-perplexity-api-key"
```

Or add to `.env` file:
```
PERPLEXITY_API_KEY=your-perplexity-api-key
```

### Free Tier

Perplexity offers free tier with limited requests. For production use, consider:
- Caching aggressively (default behavior)
- Using `--refresh-posts` only when needed
- Using file-based input for frequently updated data

## Cache Management

### View Cached Profiles

```python
from src.ai_agentic_workflow.agents import LinkedInDataFetcher

fetcher = LinkedInDataFetcher()
profiles = fetcher.list_cached_profiles()

for profile in profiles:
    print(f"URL: {profile['url']}")
    print(f"Last fetched: {profile['last_fetched']}")
    print(f"Has posts: {profile['has_posts']}")
    print(f"Has profile: {profile['has_profile']}")
```

### Manual Cache Access

```python
from src.ai_agentic_workflow.agents import LinkedInDataFetcher

fetcher = LinkedInDataFetcher()

# Get cached data for specific URL
data = fetcher.get_cached_data("https://www.linkedin.com/in/johndoe")

# Or get most recent
data = fetcher.get_cached_data()
```

### Clear Cache

Simply delete the `.linkedin_cache/` directory:
```bash
rm -rf .linkedin_cache
```

## Best Practices

1. **Fetch Once, Use Many Times**
   - Provide URL on first run
   - Subsequent runs automatically use cache
   - Only refresh when you have new posts

2. **Refresh Strategically**
   - Use `--refresh-posts` weekly/monthly for new posts
   - Use `--refresh-all` only when profile significantly changed
   - Profile data rarely changes, posts change frequently

3. **Cache Management**
   - Keep `.linkedin_cache/` in `.gitignore` (contains personal data)
   - Backup cache if switching machines
   - Clear cache if data seems stale

4. **Multiple Profiles**
   - System supports multiple cached profiles
   - Uses most recent by default
   - Specify URL to use specific profile

## Troubleshooting

### No Data Fetched

**Issue**: `--linkedin-url` doesn't fetch data

**Solutions**:
- Check PERPLEXITY_API_KEY is set
- Verify LinkedIn URL is correct and public
- Check Perplexity API quota/limits
- Try `--refresh-all` to force fetch

### Cache Not Found

**Issue**: System doesn't find cached data

**Solutions**:
- Ensure `.linkedin_cache/` directory exists
- Check `cache_metadata.json` has entries
- Verify cache files exist and are readable
- Try providing `--linkedin-url` again

### Stale Data

**Issue**: Using old cached data

**Solutions**:
- Use `--refresh-posts` to update posts
- Use `--refresh-all` to update everything
- Check `cache_metadata.json` for last_fetched timestamp

### Perplexity Errors

**Issue**: Perplexity API errors

**Solutions**:
- Check API key is valid
- Verify API quota not exceeded
- Try again later (rate limits)
- Fall back to file-based input

## Integration with Persona Extraction

The fetched LinkedIn data automatically flows into persona extraction:

```
LinkedIn URL
  ↓
LinkedInDataFetcher.fetch_linkedin_data()
  ↓
Cached data (profile, posts, resume)
  ↓
PersonaExtractor.execute()
  ↓
PersonaMemory (compact, reusable)
  ↓
BlogCreationAgent (uses persona throughout)
```

## Summary

The LinkedIn Data Fetcher provides:
- ✅ **Automatic fetching** from URLs using Perplexity
- ✅ **Smart caching** for reuse across sessions
- ✅ **Seamless integration** with persona extraction
- ✅ **Backward compatible** with file-based input
- ✅ **Refresh options** for updating data
- ✅ **Multi-profile support** with automatic selection

This makes the blog creation workflow much more convenient - fetch once, use forever (until you refresh)!
