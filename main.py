from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from transformers import pipeline
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import io

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 1. Initialize API Key (Yahan apni key paste karo)
ELEVENLABS_API_KEY = "YOUR_ELEVENLABS_API_KEY_HERE"
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# 2. Load Emotion Model globally so it doesn't reload on every request
print("Loading AI Model...")
emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
print("Model Ready!")

# Data format for incoming requests
class TextInput(BaseModel):
    text: str

@app.get("/")
async def serve_home(request: Request):
    """Serves the main HTML UI"""
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/generate")
async def generate_audio_endpoint(data: TextInput):
    """Receives text, detects emotion, and streams back the audio"""
    
    text = data.text
    
    # Detect Emotion
    result = emotion_classifier(text)
    emotion = result[0]['label']
    
    # Emotion Mapping Logic
    stability = 0.75
    similarity_boost = 0.75
    style = 0.0
    
    if emotion in ["joy", "surprise"]:
        stability = 0.3
        style = 0.6
    elif emotion == "sadness":
        stability = 0.4
        style = 0.4
    elif emotion == "anger":
        stability = 0.25
        style = 0.7
    elif emotion == "fear":
        stability = 0.3
        style = 0.5

    # Call ElevenLabs API
    audio_stream = client.text_to_speech.convert(
        text=text,
        voice_id="EXAVITQu4vr4xnSDxMaL", # Rachel
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=stability, 
            similarity_boost=similarity_boost, 
            style=style, 
            use_speaker_boost=True
        )
    )
    
    # Generator to stream the audio chunks directly to the frontend
    def iterfile():
        for chunk in audio_stream:
            if chunk:
                yield chunk

    # Return the audio file directly with a custom header for the emotion
    return StreamingResponse(
        iterfile(), 
        media_type="audio/mpeg",
        headers={"X-Emotion": emotion} # Sending emotion back to UI
    )