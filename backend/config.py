import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# API Keys
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Server Settings
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vani_assistant.db")

# Context & Memory
MAX_CONTEXT_TURNS = int(os.getenv("MAX_CONTEXT_TURNS", "15"))
GUARDRAILS_STRICT_MODE = os.getenv("GUARDRAILS_STRICT_MODE", "True").lower() in ("true", "1", "yes")

# Sarvam Voice Mapping (Language Code -> Bulbul v3 Supported Speakers: aditya, ritu, kavya, pooja, etc.)
SARVAM_VOICE_MAP = {
    "hi-IN": "ritu",         # Hindi Female Neural
    "en-IN": "kavya",        # Indian English Female Neural
    "ta-IN": "anand",        # Tamil
    "te-IN": "chaitra",      # Telugu
    "mr-IN": "ishita",       # Marathi
    "bn-IN": "rupali",       # Bengali
    "gu-IN": "pooja",        # Gujarati
    "kn-IN": "chaitra",      # Kannada
    "ml-IN": "shreya",       # Malayalam
    "pa-IN": "anand",        # Punjabi
    "default": "ritu"
}

# Edge-TTS Fallback Voice Mapping
EDGE_TTS_VOICE_MAP = {
    "hi-IN": "hi-IN-SwaraNeural",
    "en-IN": "en-IN-NeerjaNeural",
    "en-US": "en-US-JennyNeural",
    "ta-IN": "ta-IN-PallaviNeural",
    "te-IN": "te-IN-ShrutiNeural",
    "mr-IN": "mr-IN-AarohiNeural",
    "bn-IN": "bn-IN-TanishaaNeural",
    "gu-IN": "gu-IN-DhwaniNeural",
    "kn-IN": "kn-IN-SapnaNeural",
    "ml-IN": "ml-IN-SobhanaNeural",
    "default": "hi-IN-SwaraNeural"
}

def is_sarvam_configured() -> bool:
    return bool(SARVAM_API_KEY and len(SARVAM_API_KEY) > 10)

def is_gemini_configured() -> bool:
    return bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 10)
