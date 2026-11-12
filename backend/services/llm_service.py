import re
import asyncio
import logging
from typing import AsyncGenerator, List, Dict, Any
from config import GEMINI_API_KEY, is_gemini_configured

logger = logging.getLogger("llm_service")

class LLMService:
    def __init__(self):
        self._client = None
        self._init_client()

    def _init_client(self):
        if is_gemini_configured():
            try:
                from google import genai
                self._client = genai.Client(api_key=GEMINI_API_KEY)
                logger.info("Google GenAI client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI client: {e}")

    def _build_system_instruction(self, user_query: str, detected_lang: str) -> str:
        """
        Dynamically constructs system instruction tailored to:
        1. Exact Language & Dialect Matching (English -> English, Hindi -> Hindi, CG -> CG)
        2. Strict Voice Conciseness (1-2 sentences by default; long ONLY when explicitly asked)
        """
        lower = user_query.lower()

        # Check if user explicitly asked for a long or detailed explanation
        long_triggers = [
            "detail", "detailed", "explain in detail", "long answer", "long reply",
            "in depth", "elaborate", "thorough", "विस्तार", "विस्तार से", "बड़ा उत्तर",
            "बड़ा जवाब", "डिटेल", "डिटेल में", "पूरा बताव", "लम्बा", "लम्बा उत्तर"
        ]
        wants_long = any(t in lower or t in user_query for t in long_triggers)

        # Detect dialect / language category using whole-word matching
        words = set(re.findall(r"[\u0900-\u097F\w]+", user_query))
        has_devanagari = any('\u0900' <= char <= '\u097f' for char in user_query)
        cg_words = {
            "काबर", "कइसे", "कतेक", "तोर", "मोर", "हमन", "तुमन", "बर", "ला", "नइ", "झन",
            "हे", "हव", "हस", "करथें", "होइस", "कहूँ", "एती", "ओती", "लइका", "सियान", "गोठ",
            "कतका", "लागथे", "आथे", "जाथे", "बने", "अउ", "सब्बो", "बहिनी", "तिहार", "थरहा", "धान", "छेड़क", "कीरा"
        }
        is_cg = detected_lang == "cg" or bool(words & cg_words)
        is_hindi = has_devanagari and not is_cg
        is_hinglish = not has_devanagari and any(w in lower.split() for w in ["kya", "hai", "kaise", "batao", "karo", "mera", "meri", "hum", "kaun", "kaha"])
        is_english = not has_devanagari and not is_hinglish

        # 1. Length Directive
        if wants_long:
            length_directive = "LENGTH: The user explicitly requested a detailed explanation. Provide a thorough, informative, multi-sentence response (4 to 6 sentences)."
        else:
            length_directive = "LENGTH: KEEP YOUR RESPONSE CRISP, SHORT, AND TO THE POINT (EXACTLY 1 TO 2 SENTENCES, MAXIMUM 25-35 WORDS). Do NOT give long paragraphs, lists, or filler introductions. As a voice assistant, speak directly and concisely."

        # 2. Strict Language Directive
        if is_cg:
            lang_directive = """LANGUAGE DIRECTIVE:
The user asked in CHHATTISGARHI (छत्तीसगढ़ी).
You MUST reply ONLY in AUTHENTIC CHHATTISGARHI (Devanagari script) with regional grammatical vocabulary (such as बर, ला, हे, हमन, तोर, करथें, बतावत हन, नइ).
Do NOT reply in standard textbook Hindi or English!"""
        elif is_hindi:
            lang_directive = """LANGUAGE DIRECTIVE:
The user asked in HINDI (हिन्दी).
You MUST reply ONLY in pure, natural, grammatically correct HINDI (Devanagari script).
Do NOT reply in English or Roman script!"""
        elif is_hinglish:
            lang_directive = """LANGUAGE DIRECTIVE:
The user asked in HINGLISH.
Reply in natural conversational Hinglish (Roman script) matching the user's casual tone."""
        else:
            lang_directive = """LANGUAGE DIRECTIVE:
The user asked in ENGLISH.
You MUST reply ONLY in clear, natural, grammatically fluent ENGLISH.
Do NOT reply in Hindi or Devanagari script!"""

        return f"""You are Vani AI, an intelligent real-time conversational voice assistant.
Your text is directly converted into spoken speech audio for the user.

{length_directive}

{lang_directive}

FORMATTING RULES:
- Do NOT use markdown code blocks, asterisks (*), hashtags (#), bullet points (-), or URLs.
- Deliver speech-friendly, natural conversational sentences."""

    async def stream_response(
        self,
        user_query: str,
        chat_history: List[Dict[str, Any]] = None,
        detected_lang: str = "en-IN"
    ) -> AsyncGenerator[str, None]:
        """
        Streams response tokens from Gemini models with precise language & length enforcement.
        """
        if chat_history is None:
            chat_history = []

        system_instruction = self._build_system_instruction(user_query, detected_lang)

        candidate_models = ["gemini-2.5-flash-lite", "gemini-2.5-flash", "gemini-3.6-flash"]

        # 1. Live Google GenAI Client Streaming
        if self._client and is_gemini_configured():
            from google.genai import types

            contents = []
            for turn in chat_history:
                role = turn.get("role", "user")
                parts = turn.get("parts", [{}])
                text = parts[0].get("text", "") if parts else ""
                if text:
                    contents.append(types.Content(
                        role="user" if role == "user" else "model",
                        parts=[types.Part.from_text(text=text)]
                    ))

            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_query)]
            ))

            for model_name in candidate_models:
                try:
                    logger.info(f"Generating voice response with model {model_name}...")
                    response = self._client.models.generate_content_stream(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.3,
                            max_output_tokens=600,
                            thinking_config=types.ThinkingConfig(thinking_budget=0)
                        )
                    )

                    has_yielded = False
                    for chunk in response:
                        if chunk.text:
                            has_yielded = True
                            yield chunk.text
                            await asyncio.sleep(0.01)

                    if has_yielded:
                        return
                except Exception as e:
                    logger.warning(f"Gemini model {model_name} streaming error: {e}. Trying fallback candidate...")
                    continue

        # 2. Local Fallback Generator
        lower = user_query.lower()
        has_devanagari = any('\u0900' <= char <= '\u097f' for char in user_query)
        is_cg = detected_lang == "cg" or any(m in user_query for m in ["काबर", "कइसे", "कतेक", "तोर", "मोर", "हमन", "तुमन", "बर", "ला", "नइ", "झन", "हे", "हव", "करथें"])
        is_hindi = has_devanagari and not is_cg

        clean_query = user_query.rstrip("?.! ")
        if is_cg:
            fallback = f"तुमन के सवाल बर पूरा समाधान हे। वाणी एआई छत्तीसगढ़ी म सबले बने सलाह देहे बर तइयार हे।"
        elif is_hindi:
            fallback = f"आपके प्रश्न '{clean_query}' का उत्तर यह है कि वाणी एआई आपको सटीक जानकारी देने के लिए तत्पर है।"
        else:
            fallback = f"Regarding your question about '{clean_query}', Vani AI provides concise, accurate voice assistance."

        for word in fallback.split(" "):
            yield word + " "
            await asyncio.sleep(0.02)

# Singleton Instance
llm_service = LLMService()
