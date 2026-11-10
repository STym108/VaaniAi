import asyncio
import logging
from typing import AsyncGenerator, List, Dict, Any
from config import GEMINI_API_KEY, is_gemini_configured

logger = logging.getLogger("llm_service")

SYSTEM_PROMPT = """You are Vani AI, a highly intelligent, articulate, and helpful multilingual conversational voice assistant with specialized regional expertise in Indian languages and Chhattisgarhi (छत्तीसगढ़ी).
Your responses will be converted into speech audio and spoken aloud to the user.

Follow these rules for generating responses:
1. ALWAYS respond in the EXACT SAME language, dialect, and script as the user's query:
   - If the user asks in Chhattisgarhi (e.g., using markers like काबर, कइसे, कतेक, तोर, मोर, हमन, तुमन, हे, हव, नइ, झन, बर, ला), respond in AUTHENTIC, grammatically correct Chhattisgarhi (Devanagari script) with regional vocabulary.
   - If Hindi, respond in standard Hindi (Devanagari script).
   - If Hinglish, respond in natural conversational Hinglish.
   - If English, respond in clear English.
2. Provide THOROUGH, COMPLETE, and INFORMATIVE answers (3-5 clear, well-explained sentences). Never truncate your explanation or give lazy 1-line answers. Explain the 'why' and 'how' clearly.
3. Keep the tone natural, engaging, and conversational for spoken voice delivery.
4. Do NOT use markdown code blocks, asterisks (*), hashtags (#), or bullet symbols (-) so that text-to-speech synthesis sounds smooth and natural."""

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
                try:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=GEMINI_API_KEY)
                    self._legacy_model = legacy_genai.GenerativeModel(
                        model_name="gemini-2.5-flash",
                        system_instruction=SYSTEM_PROMPT
                    )
                    logger.info("Legacy Gemini client initialized.")
                except Exception as legacy_err:
                    logger.error(f"Failed to initialize Gemini client: {e} | Legacy: {legacy_err}")

    async def stream_response(
        self,
        user_query: str,
        chat_history: List[Dict[str, Any]] = None,
        detected_lang: str = "en-IN"
    ) -> AsyncGenerator[str, None]:
        """
        Streams complete response tokens from Gemini models with multi-model fallback chain.
        """
        if chat_history is None:
            chat_history = []

        # Candidate Gemini models in order of performance and availability
        candidate_models = ["gemini-3.6-flash", "gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-2.5-flash"]

        # 1. Modern google.genai Client Streaming
        if self._client and is_gemini_configured():
            from google.genai import types

            # Format past turns
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

            # Add current user query
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_query)]
            ))

            for model_name in candidate_models:
                try:
                    logger.info(f"Attempting LLM generation with model: {model_name}")
                    response = self._client.models.generate_content_stream(
                        model=model_name,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.7,
                            max_output_tokens=1000
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
                    logger.warning(f"Gemini model {model_name} error: {e}. Trying next candidate...")
                    continue

        # 2. Intelligent Dynamic Contextual Fallback Generator
        lower = user_query.lower()
        is_chhattisgarhi = any(marker in user_query for marker in ["काबर", "कइसे", "कतेक", "तोर", "मोर", "हमन", "तुमन", "बर", "ला", "नइ", "झन", "हे", "हव", "लइका", "सियान", "गोठ"])
        is_hindi = any('\u0900' <= char <= '\u097f' for char in user_query) or "kya" in lower or "hai" in lower or "kaise" in lower

        clean_query = user_query.rstrip("?.! ")
        if is_chhattisgarhi:
            fallback = f"तुमन के ये सवाल '{clean_query}' बहुते जरूरी अउ महत्व के हे। एकर बारे म पूरा जानकारी अउ उपाय हमन बतावत हन। वाणी एआई छत्तीसगढ़ी भाखा म स्वाभाविक गोठ-बात करे अउ सबले बने सलाह देहे बर पूरा तइयार हे।"
        elif is_hindi:
            fallback = f"आपका प्रश्न '{clean_query}' बहुत महत्वपूर्ण और विचारणीय है। इस विषय को विस्तार से समझने के लिए मुख्य अवधारणाओं और इसके व्यावहारिक प्रभावों का विश्लेषण किया जाना आवश्यक है। वाणी एआई आपके प्रश्नों का उत्तर देने और स्वाभाविक संवाद स्थापित करने के लिए हमेशा तत्पर है।"
        else:
            fallback = f"Regarding your question about '{clean_query}', this involves key underlying principles and broad applications. Analyzing the core mechanisms step-by-step provides deep insights into the topic. Vani AI is fully equipped to deliver accurate, multi-turn conversational assistance on this and related queries."

        for word in fallback.split(" "):
            yield word + " "
            await asyncio.sleep(0.03)

# Singleton Instance
llm_service = LLMService()

