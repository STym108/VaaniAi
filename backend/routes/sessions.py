from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import ChatSession, ConversationTurn
from services.memory_service import memory_manager

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])

@router.get("/")
def list_sessions(db: Session = Depends(get_db)):
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).limit(20).all()
    return [
        {
            "id": s.id,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
            "total_turns": s.total_turns,
            "language_preference": s.language_preference
        }
        for s in sessions
    ]

@router.get("/{session_id}")
def get_session_history(session_id: str, db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    turns = db.query(ConversationTurn).filter(ConversationTurn.session_id == session_id).order_by(ConversationTurn.turn_index.asc()).all()
    return {
        "session_id": session.id,
        "total_turns": session.total_turns,
        "turns": [
            {
                "id": t.id,
                "turn_index": t.turn_index,
                "user_transcript": t.user_transcript,
                "assistant_response": t.assistant_response,
                "detected_language": t.detected_language,
                "latency_ttfa_ms": t.latency_ttfa_ms,
                "timestamp": t.timestamp.isoformat()
            }
            for t in turns
        ]
    }

@router.delete("/{session_id}")
async def clear_session(session_id: str, db: Session = Depends(get_db)):
    await memory_manager.clear_session(session_id)
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()
    return {"status": "cleared", "session_id": session_id}
