import base64
import httpx
import logging
import edge_tts
from typing import Optional
from config import SARVAM_API_KEY, SARVAM_VOICE_MAP, EDGE_TTS_VOICE_MAP, is_sarvam_configured

logger = logging.getLogger("tts_service")

class TTSService:
    def __init__(self):
        self.api_url = "https://api.sarvam.ai/text-to-speech"

    async def synthesize_speech(self, text: str, language_code: str = "hi-IN") -> bytes:
        """
        Synthesizes text into speech audio bytes using Sarvam AI Bulbul v2 (with Edge-TTS fallback).
        """
        if not text.strip():
            return b""

        # 1. Live Sarvam AI Bulbul API Call (if configured)
        if is_sarvam_configured():
            try:
                # If text contains Devanagari script (Hindi / Chhattisgarhi), enforce hi-IN and ritu
                has_devanagari = any('\u0900' <= char <= '\u097f' for char in text)
                if has_devanagari:
                    target_lang = "hi-IN"
                    speaker = "ritu"
                else:
                    speaker = SARVAM_VOICE_MAP.get(language_code, SARVAM_VOICE_MAP["default"])
                    target_lang = language_code if language_code in SARVAM_VOICE_MAP else "en-IN"

                payload = {
                    "inputs": [text[:500]],
                    "target_language_code": target_lang,
                    "speaker": speaker,
                    "model": "bulbul:v3",
                    "speech_sample_rate": 16000,
                    "enable_preprocessing": True
                }

                headers = {
                    "api-subscription-key": SARVAM_API_KEY,
                    "Content-Type": "application/json"
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(self.api_url, json=payload, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        audios = data.get("audios", [])
                        if audios:
                            return base64.b64decode(audios[0])
                    else:
                        logger.warning(f"Sarvam TTS returned {response.status_code}: {response.text}")
            except Exception as e:
                logger.error(f"Error calling Sarvam TTS: {e}")

        # 2. Edge-TTS Fallback (Free, High-Quality Neural Voices)
        try:
            voice = EDGE_TTS_VOICE_MAP.get(language_code, EDGE_TTS_VOICE_MAP["default"])
            communicate = edge_tts.Communicate(text, voice)
            audio_bytes = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]
            return audio_bytes
        except Exception as e:
            logger.error(f"Edge-TTS fallback synthesis error: {e}")
            return b""

# Singleton Instance
tts_service = TTSService()
