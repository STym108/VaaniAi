import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from config import MAX_CONTEXT_TURNS
from database import SessionLocal
from models import ChatSession, ConversationTurn

class TurnData:
    def __init__(self, role: str, text: str, language: str = "en-IN", latency_ms: int = 0):
        self.role = role # 'user' or 'model' / 'assistant'
        self.text = text
        self.language = language
        self.latency_ms = latency_ms
        self.timestamp = datetime.now(timezone.utc)

class SessionMemoryManager:
    def __init__(self, max_turns: int = MAX_CONTEXT_TURNS):
        self.max_turns = max_turns
        self._memory_store: Dict[str, List[TurnData]] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_session(self, session_id: str) -> str:
        async with self._lock:
            if session_id not in self._memory_store:
                self._memory_store[session_id] = []
                # Ensure session in DB
                db = SessionLocal()
                try:
                    existing = db.query(ChatSession).filter(ChatSession.id == session_id).first()
                    if not existing:
                        new_session = ChatSession(id=session_id)
                        db.add(new_session)
                        db.commit()
                except Exception as e:
                    db.rollback()
                finally:
                    db.close()
        return session_id

    async def append_turn(
        self,
        session_id: str,
        user_text: str,
        assistant_text: str,
        detected_lang: str = "en-IN",
        latency_ms: int = 0
    ):
        async with self._lock:
            if session_id not in self._memory_store:
                self._memory_store[session_id] = []

            # Append User and Assistant turns
            self._memory_store[session_id].append(TurnData(role="user", text=user_text, language=detected_lang))
            self._memory_store[session_id].append(TurnData(role="model", text=assistant_text, language=detected_lang, latency_ms=latency_ms))

            # Prune sliding window if exceeding max turns (keep most recent turns)
            if len(self._memory_store[session_id]) > self.max_turns * 2:
                self._memory_store[session_id] = self._memory_store[session_id][-self.max_turns * 2:]

        # Persist to database in background
        self._persist_turn_db(session_id, user_text, assistant_text, detected_lang, latency_ms)

    def _persist_turn_db(self, session_id: str, user_text: str, assistant_text: str, lang: str, latency: int):
        db = SessionLocal()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                session = ChatSession(id=session_id)
                db.add(session)
                db.flush()

            session.total_turns += 1
            session.updated_at = datetime.now(timezone.utc)

            turn = ConversationTurn(
                session_id=session_id,
                turn_index=session.total_turns,
                user_transcript=user_text,
                assistant_response=assistant_text,
                detected_language=lang,
                latency_ttfa_ms=latency
            )
            db.add(turn)
            db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    async def get_gemini_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Formats conversational turns for Google Gemini multi-turn history.
        """
        async with self._lock:
            turns = self._memory_store.get(session_id, [])
            formatted = []
            for t in turns:
                role = "user" if t.role == "user" else "model"
                formatted.append({
                    "role": role,
                    "parts": [{"text": t.text}]
                })
            return formatted

    async def clear_session(self, session_id: str):
        async with self._lock:
            if session_id in self._memory_store:
                self._memory_store[session_id] = []

# Singleton Instance
memory_manager = SessionMemoryManager()
