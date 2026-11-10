import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    language_preference = Column(String(20), default="auto")
    total_turns = Column(Integer, default=0)

    # Relationship to conversation turns
    turns = relationship("ConversationTurn", back_populates="session", cascade="all, delete-orphan")
    guardrail_logs = relationship("GuardrailAudit", back_populates="session", cascade="all, delete-orphan")

class ConversationTurn(Base):
    __tablename__ = "conversation_turns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    turn_index = Column(Integer, default=0)
    user_transcript = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    detected_language = Column(String(20), default="en-IN")
    latency_ttfa_ms = Column(Integer, default=0)
    guardrail_passed = Column(Boolean, default=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="turns")

class GuardrailAudit(Base):
    __tablename__ = "guardrail_audits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=True)
    input_text = Column(Text, nullable=False)
    violation_type = Column(String(50), nullable=False) # 'injection', 'pii', 'toxicity'
    flagged_terms = Column(Text, default="")
    action_taken = Column(String(50), default="blocked") # 'blocked', 'redacted', 'warned'
    timestamp = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="guardrail_logs")
