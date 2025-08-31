import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import openai
import os
import requests
import re
from pathlib import Path
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# --- Configuration ---
ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)

# Mount the assets directory to serve static files
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

# Add CORS middleware to allow requests from the HTML file opened locally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["null", "file://"],  # "null" for file:// origins in some browsers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Key Setup ---
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    logging.error("OPENAI_API_KEY not found in .env file. Please add it.")
    # You might want to exit here in a real application
    # exit(1)

# --- Pydantic Models for Request Bodies ---
class ImageRequest(BaseModel):
    scene_number: int
    prompt: dict

class AudioRequest(BaseModel):
    scene_number: int
    text: str

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Asset generation server is running. Open buddha_100_series_workflow.html in your browser."}

@app.post("/generate-image")
async def generate_image(req: ImageRequest):
    """
    Generates an image using DALL-E 3 based on the provided prompt.
    """
    if not openai.api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key is not configured.")

    scene_num = req.scene_number
    prompt_data = req.prompt
    logging.info(f"Received image generation request for scene {scene_num}")

    try:
        # Construct a detailed prompt from the structured data
        prompt_text = (
            f"{prompt_data.get('main_subject', '')}, {prompt_data.get('setting', '')}. "
            f"Lighting: {prompt_data.get('lighting', '')}. "
            f"Color Palette: {prompt_data.get('color_palette', '')}. "
            f"Style: {', '.join(prompt_data.get('style_modifiers', []))}, cinematic, contemplative illustration."
        )

        desc_slug = re.sub(r'[^a-zA-Z0-9]+', '_', prompt_data.get('main_subject', 'scene').lower())[:50].strip('_')
        img_path = ASSETS_DIR / f"scene_{scene_num:02d}_{desc_slug}.png"
        
        logging.info(f"Generating image for scene {scene_num} with prompt: '{prompt_text[:100]}...'")

        response = await openai.images.generate(
            model="dall-e-3",
            prompt=prompt_text,
            n=1,
            size="1792x1024",  # Using a 16:9 aspect ratio size available for DALL-E 3
            quality="standard",
        )
        
        image_url = response.data[0].url
        
        # Download the image
        img_data = requests.get(image_url, timeout=60).content
        with open(img_path, "wb") as f:
            f.write(img_data)
        
        logging.info(f"Successfully saved image for scene {scene_num} to {img_path}")
        
        # Return the local URL for the frontend
        return {"url": f"/assets/{img_path.name}"}

    except Exception as e:
        logging.error(f"Image generation failed for scene {scene_num}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-audio")
async def generate_audio(req: AudioRequest):
    """
    Generates audio using OpenAI's TTS model.
    """
    if not openai.api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key is not configured.")

    scene_num = req.scene_number
    text = req.text
    logging.info(f"Received audio generation request for scene {scene_num}")

    if not text or not text.strip():
        logging.warning(f"Skipping audio generation for scene {scene_num} due to empty text.")
        raise HTTPException(status_code=400, detail="Narration text cannot be empty.")

    try:
        text_slug = re.sub(r'[^a-zA-Z0-9]+', '_', text[:25].lower()).strip('_')
        audio_path = ASSETS_DIR / f"scene_{scene_num:02d}_{text_slug}.mp3"

        logging.info(f"Generating audio for scene {scene_num} with text: '{text[:50]}...'")

        response = await openai.audio.speech.create(
            model="tts-1",
            voice="alloy", # Available voices: alloy, echo, fable, onyx, nova, shimmer
            input=text,
        )

        # Stream the audio data to a file
        response.stream_to_file(audio_path)
        
        logging.info(f"Successfully saved audio for scene {scene_num} to {audio_path}")
        
        return {"url": f"/assets/{audio_path.name}"}

    except Exception as e:
        logging.error(f"Audio generation failed for scene {scene_num}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- Main Execution ---
if __name__ == "__main__":
    print("--- Asset Generation Server ---")
    print(f"Serving assets from: {ASSETS_DIR.resolve()}")
    print("To start, open the 'buddha_100_series_workflow.html' file in your web browser.")
    print("Make sure your .env file is in the same directory with your OPENAI_API_KEY.")
    print("Server running on http://localhost:8000")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)