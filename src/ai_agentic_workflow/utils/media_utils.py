import os
import json
import logging
import re
from typing import List, Dict, Any

import requests
import openai
import google.generativeai as genai

from .env_reader import get_env_variable

logger = logging.getLogger(__name__)


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
    return slug.strip("_")


def generate_image(prompt: str, api_key: str, model: str = "dall-e-3") -> bytes:
    """Generate an image using OpenAI's image API and return raw bytes."""
    client = openai.OpenAI(api_key=api_key)
    response = client.images.generate(prompt=prompt, n=1, model=model)
    url = response.data[0].url
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.content


def generate_audio(text: str, api_key: str, model: str = "gemini-2.5-pro-preview-tts") -> bytes:
    """Generate speech audio using Gemini TTS and return raw bytes."""
    genai.configure(api_key=api_key)
    model_obj = genai.GenerativeModel(model)
    response = model_obj.generate_content(text)
    try:
        audio_bytes = response.candidates[0].audio
    except Exception as exc:  # pragma: no cover - depends on API
        logger.error("Unexpected audio response: %s", exc)
        raise
    return audio_bytes


def create_media_files(visual_prompts: List[Dict[str, Any]],
                       script_scenes: List[Dict[str, Any]],
                       output_dir: str = "media") -> None:
    """Generate image and audio files for each scene."""
    openai_key = get_env_variable("OPENAI_API_KEY")
    gemini_key = get_env_variable("GEMINI_API_KEY")
    os.makedirs(output_dir, exist_ok=True)

    for prompt in visual_prompts:
        scene_num = int(prompt.get("scene_number", 0))
        desc = prompt.get("main_subject", "scene")
        slug = _slugify(desc)[:40]
        text_prompt = json.dumps(prompt)
        try:
            img_bytes = generate_image(text_prompt, api_key=openai_key)
            img_path = os.path.join(output_dir, f"{scene_num:02d}_{slug}.png")
            with open(img_path, "wb") as f:
                f.write(img_bytes)
            logger.info("Saved image %s", img_path)
        except Exception as exc:  # pragma: no cover - network failures not tested
            logger.error("Failed generating image for scene %s: %s", scene_num, exc)

    for scene in script_scenes:
        scene_num = int(scene.get("scene_number", 0))
        narration = scene.get("narration", "")
        slug = _slugify(scene.get("title", "scene"))[:40]
        try:
            audio_bytes = generate_audio(narration, api_key=gemini_key)
            audio_path = os.path.join(output_dir, f"{scene_num:02d}_{slug}.mp3")
            with open(audio_path, "wb") as f:
                f.write(audio_bytes)
            logger.info("Saved audio %s", audio_path)
        except Exception as exc:  # pragma: no cover
            logger.error("Failed generating audio for scene %s: %s", scene_num, exc)
