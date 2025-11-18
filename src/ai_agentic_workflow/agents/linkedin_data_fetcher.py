"""
LinkedIn Data Fetcher - Automatically fetches and caches LinkedIn data.

Uses Perplexity AI for web search to fetch LinkedIn profile and posts,
then caches the data locally for reuse.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from ..clients.perplexity_client import DualModelPerplexityClient
from ..logging import get_logger


@dataclass
class LinkedInDataCache:
    """Cache metadata for LinkedIn data."""
    profile_url: str
    posts_file: Optional[str] = None
    profile_file: Optional[str] = None
    resume_file: Optional[str] = None
    last_fetched: Optional[str] = None
    fetch_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "profile_url": self.profile_url,
            "posts_file": self.posts_file,
            "profile_file": self.profile_file,
            "resume_file": self.resume_file,
            "last_fetched": self.last_fetched,
            "fetch_count": self.fetch_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LinkedInDataCache':
        return cls(**data)


class LinkedInDataFetcher:
    """
    Fetches LinkedIn data using Perplexity AI and caches it locally.
    
    Automatically checks for cached data and refreshes if needed.
    """
    
    def __init__(self, cache_dir: str = ".linkedin_cache"):
        """
        Initialize LinkedIn Data Fetcher.
        
        Args:
            cache_dir: Directory to store cached LinkedIn data
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.logger = get_logger(__name__)
        
        # Initialize Perplexity client
        try:
            self.perplexity_client = DualModelPerplexityClient(
                reasoning_model="sonar-pro",
                concept_model="sonar",
                default_model="reasoning",
            )
            self.perplexity_available = True
        except Exception as e:
            self.logger.warning(f"Perplexity client not available: {e}")
            self.perplexity_available = False
        
        # Cache metadata file
        self.cache_metadata_file = self.cache_dir / "cache_metadata.json"
        self._load_cache_metadata()
    
    def _load_cache_metadata(self):
        """Load cache metadata from file."""
        if self.cache_metadata_file.exists():
            try:
                with open(self.cache_metadata_file, 'r') as f:
                    data = json.load(f)
                    self.cache_metadata = {
                        url: LinkedInDataCache.from_dict(cache_data)
                        for url, cache_data in data.items()
                    }
            except Exception as e:
                self.logger.warning(f"Failed to load cache metadata: {e}")
                self.cache_metadata = {}
        else:
            self.cache_metadata = {}
    
    def _save_cache_metadata(self):
        """Save cache metadata to file."""
        try:
            data = {
                url: cache.to_dict()
                for url, cache in self.cache_metadata.items()
            }
            with open(self.cache_metadata_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save cache metadata: {e}")
    
    def _get_cache_key(self, profile_url: str) -> str:
        """Generate cache key from profile URL."""
        # Extract username from URL
        match = re.search(r'linkedin\.com/in/([^/?]+)', profile_url)
        if match:
            return match.group(1)
        # Fallback: use URL hash
        return str(hash(profile_url))
    
    def _get_cache_files(self, cache_key: str) -> Tuple[Path, Path, Path]:
        """Get cache file paths for a cache key."""
        posts_file = self.cache_dir / f"{cache_key}_posts.txt"
        profile_file = self.cache_dir / f"{cache_key}_profile.txt"
        resume_file = self.cache_dir / f"{cache_key}_resume.txt"
        return posts_file, profile_file, resume_file
    
    def fetch_linkedin_data(
        self,
        profile_url: Optional[str] = None,
        refresh: bool = False,
        refresh_posts: bool = True
    ) -> Dict[str, Any]:
        """
        Fetch LinkedIn data, using cache if available.
        
        Args:
            profile_url: LinkedIn profile URL
            refresh: Force refresh all data
            refresh_posts: Refresh posts even if profile is cached
        
        Returns:
            Dictionary with 'linkedin_posts', 'linkedin_profile', 'resume'
        """
        if not profile_url:
            # Check for existing cache (any user)
            if self.cache_metadata:
                # Use most recently fetched
                latest = max(
                    self.cache_metadata.values(),
                    key=lambda c: c.last_fetched or ""
                )
                profile_url = latest.profile_url
                self.logger.info(f"Using cached profile: {profile_url}")
            else:
                return {}
        
        cache_key = self._get_cache_key(profile_url)
        posts_file, profile_file, resume_file = self._get_cache_files(cache_key)
        
        # Initialize cache entry if needed
        if profile_url not in self.cache_metadata:
            self.cache_metadata[profile_url] = LinkedInDataCache(
                profile_url=profile_url,
                posts_file=str(posts_file) if posts_file.exists() else None,
                profile_file=str(profile_file) if profile_file.exists() else None,
                resume_file=str(resume_file) if resume_file.exists() else None,
            )
        
        cache = self.cache_metadata[profile_url]
        result = {}
        
        # Check and load cached profile
        if not refresh and profile_file.exists():
            self.logger.info(f"Loading cached profile from {profile_file}")
            with open(profile_file, 'r', encoding='utf-8') as f:
                result['linkedin_profile'] = f.read()
            cache.profile_file = str(profile_file)
        elif self.perplexity_available:
            self.logger.info(f"Fetching LinkedIn profile from {profile_url}")
            profile_data = self._fetch_profile(profile_url)
            if profile_data:
                result['linkedin_profile'] = profile_data
                with open(profile_file, 'w', encoding='utf-8') as f:
                    f.write(profile_data)
                cache.profile_file = str(profile_file)
        
        # Check and load cached posts
        if not refresh and not refresh_posts and posts_file.exists():
            self.logger.info(f"Loading cached posts from {posts_file}")
            posts = self._load_posts_file(posts_file)
            if posts:
                result['linkedin_posts'] = posts
                cache.posts_file = str(posts_file)
        elif self.perplexity_available:
            self.logger.info(f"Fetching LinkedIn posts from {profile_url}")
            posts = self._fetch_posts(profile_url)
            if posts:
                result['linkedin_posts'] = posts
                with open(posts_file, 'w', encoding='utf-8') as f:
                    # Save as JSON array
                    json.dump(posts, f, indent=2, ensure_ascii=False)
                cache.posts_file = str(posts_file)
        
        # Check and load cached resume (optional)
        if resume_file.exists():
            self.logger.info(f"Loading cached resume from {resume_file}")
            with open(resume_file, 'r', encoding='utf-8') as f:
                result['resume'] = f.read()
            cache.resume_file = str(resume_file)
        elif self.perplexity_available:
            # Try to fetch resume from profile
            resume_data = self._fetch_resume(profile_url)
            if resume_data:
                result['resume'] = resume_data
                with open(resume_file, 'w', encoding='utf-8') as f:
                    f.write(resume_data)
                cache.resume_file = str(resume_file)
        
        # Update cache metadata
        cache.last_fetched = datetime.now().isoformat()
        cache.fetch_count += 1
        self._save_cache_metadata()
        
        return result
    
    def _fetch_profile(self, profile_url: str) -> Optional[str]:
        """Fetch LinkedIn profile using Perplexity."""
        if not self.perplexity_available:
            return None
        
        try:
            prompt = f"""Extract comprehensive professional information from this LinkedIn profile.

LinkedIn Profile URL: {profile_url}

Please provide:
1. Full name and current role/title
2. Complete work experience with company names, roles, dates, and key responsibilities
3. Education background
4. Skills and technical expertise
5. Certifications
6. Summary/about section
7. Any notable achievements or projects mentioned

Format the output as a detailed professional profile text that can be used for persona extraction.
Focus on extracting all work experience details, technical skills, and career progression."""

            llm = self.perplexity_client.get_llm()
            response = llm.invoke(prompt)
            profile_text = str(response.content) if hasattr(response, 'content') else str(response)
            
            self.logger.info(f"Fetched profile data ({len(profile_text)} chars)")
            return profile_text
            
        except Exception as e:
            self.logger.error(f"Error fetching profile: {e}")
            return None
    
    def _fetch_posts(self, profile_url: str, max_posts: int = 20) -> Optional[List[str]]:
        """Fetch recent LinkedIn posts using Perplexity."""
        if not self.perplexity_available:
            return None
        
        try:
            prompt = f"""Extract the most recent LinkedIn posts from this profile.

LinkedIn Profile URL: {profile_url}

Please provide the last {max_posts} posts from this LinkedIn profile.
For each post, include:
- The full text content
- Any hashtags
- Engagement context if available

Return the posts as a JSON array of strings, where each string is a complete post.
Example format: ["Post 1 text here", "Post 2 text here", ...]

If you cannot access the posts directly, provide what information you can find about their recent activity or content themes."""

            llm = self.perplexity_client.get_llm()
            response = llm.invoke(prompt)
            response_text = str(response.content) if hasattr(response, 'content') else str(response)
            
            # Try to parse as JSON
            try:
                # Remove markdown code blocks if present
                cleaned = response_text.strip()
                if cleaned.startswith("```"):
                    lines = cleaned.split("\n")
                    cleaned = "\n".join(lines[1:-1])
                
                # Try to find JSON array
                json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
                if json_match:
                    posts = json.loads(json_match.group())
                    if isinstance(posts, list):
                        self.logger.info(f"Fetched {len(posts)} posts")
                        return posts
            except json.JSONDecodeError:
                pass
            
            # Fallback: split by lines or paragraphs
            posts = [line.strip() for line in response_text.split('\n') if line.strip()]
            if posts:
                self.logger.info(f"Fetched {len(posts)} posts (parsed from text)")
                return posts[:max_posts]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching posts: {e}")
            return None
    
    def _fetch_resume(self, profile_url: str) -> Optional[str]:
        """Try to fetch resume/CV information from profile."""
        if not self.perplexity_available:
            return None
        
        try:
            prompt = f"""Extract resume/CV information from this LinkedIn profile.

LinkedIn Profile URL: {profile_url}

Please provide a comprehensive resume-style summary including:
1. Professional summary
2. Work experience in chronological order with detailed responsibilities
3. Education
4. Skills (technical and soft skills)
5. Certifications
6. Projects and achievements

Format as a professional resume document."""

            llm = self.perplexity_client.get_llm()
            response = llm.invoke(prompt)
            resume_text = str(response.content) if hasattr(response, 'content') else str(response)
            
            if len(resume_text) > 100:  # Only return if substantial content
                self.logger.info(f"Fetched resume data ({len(resume_text)} chars)")
                return resume_text
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error fetching resume: {e}")
            return None
    
    def _load_posts_file(self, posts_file: Path) -> Optional[List[str]]:
        """Load posts from file (supports JSON or plain text)."""
        try:
            with open(posts_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try JSON first
            try:
                posts_data = json.loads(content)
                if isinstance(posts_data, list):
                    return posts_data
                elif isinstance(posts_data, dict) and "posts" in posts_data:
                    return posts_data["posts"]
            except json.JSONDecodeError:
                pass
            
            # Fallback: plain text (one per line)
            posts = [line.strip() for line in content.split('\n') if line.strip()]
            return posts if posts else None
            
        except Exception as e:
            self.logger.error(f"Error loading posts file: {e}")
            return None
    
    def get_cached_data(self, profile_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get cached LinkedIn data without fetching.
        
        Args:
            profile_url: Specific profile URL, or None for most recent
        
        Returns:
            Dictionary with cached data
        """
        if not profile_url:
            if self.cache_metadata:
                latest = max(
                    self.cache_metadata.values(),
                    key=lambda c: c.last_fetched or ""
                )
                profile_url = latest.profile_url
            else:
                return {}
        
        cache_key = self._get_cache_key(profile_url)
        posts_file, profile_file, resume_file = self._get_cache_files(cache_key)
        
        result = {}
        
        if profile_file.exists():
            with open(profile_file, 'r', encoding='utf-8') as f:
                result['linkedin_profile'] = f.read()
        
        if posts_file.exists():
            posts = self._load_posts_file(posts_file)
            if posts:
                result['linkedin_posts'] = posts
        
        if resume_file.exists():
            with open(resume_file, 'r', encoding='utf-8') as f:
                result['resume'] = f.read()
        
        return result
    
    def list_cached_profiles(self) -> List[Dict[str, Any]]:
        """List all cached profiles."""
        profiles = []
        for url, cache in self.cache_metadata.items():
            profiles.append({
                "url": url,
                "last_fetched": cache.last_fetched,
                "fetch_count": cache.fetch_count,
                "has_posts": cache.posts_file and Path(cache.posts_file).exists(),
                "has_profile": cache.profile_file and Path(cache.profile_file).exists(),
                "has_resume": cache.resume_file and Path(cache.resume_file).exists(),
            })
        return profiles
