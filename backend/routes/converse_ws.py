import time
import json
import base64
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.stt_service import stt_service
from services.guardrails_service import guardrails
from services.memory_service import memory_manager
from services.llm_service import llm_service
from services.stream_chunker import stream_chunker
from services.tts_service import tts_service
from database import SessionLocal
from models import GuardrailAudit

logger = logging.getLogger("converse_ws")
router = APIRouter()

@router.websocket("/ws/converse")
async def websocket_converse(websocket: WebSocket):
    await websocket.accept()
    session_id = "default-session"
    
    try:
        while True:
            # Receive message (JSON or binary)
            message_raw = await websocket.receive_text()
            data = json.loads(message_raw)
            msg_type = data.get("type", "")

            if msg_type == "init":
                session_id = data.get("session_id", session_id)
                await memory_manager.get_or_create_session(session_id)
                await websocket.send_json({
                    "type": "session_ready",
                    "session_id": session_id
                })
                continue

            start_time = time.time()
            user_text = ""
            detected_lang = "en-IN"

            # 1. Audio Query Flow
            if msg_type == "audio_query":
                audio_base64 = data.get("audio_base64", "")
                audio_bytes = base64.b64decode(audio_base64)
                
                # Step A: Sarvam STT & Language Detection
                stt_res = await stt_service.transcribe_audio(audio_bytes)
                user_text = stt_res.text
                detected_lang = stt_res.language_code

                # Refine dialect detection for Chhattisgarhi
                if user_text and any(m in user_text for m in ["काबर", "कइसे", "कतेक", "तोर", "मोर", "हमन", "तुमन", "बर", "ला", "नइ", "झन", "हे", "हव", "करथें", "होइस", "कतका", "लागथे", "आथे", "जाथे"]):
                    detected_lang = "cg"

                await websocket.send_json({
                    "type": "stt_result",
                    "text": user_text,
                    "transcript": user_text,
                    "language_code": detected_lang,
                    "confidence": stt_res.confidence
                })

            # 2. Text Query Flow
            elif msg_type == "text_query":
                user_text = data.get("text", "")
                has_devanagari = any('\u0900' <= char <= '\u097f' for char in user_text)
                is_cg = any(m in user_text for m in ["काबर", "कइसे", "कतेक", "तोर", "मोर", "हमन", "तुमन", "बर", "ला", "नइ", "झन", "हे", "हव", "करथें", "होइस", "कतका", "लागथे", "आथे", "जाथे"])
                if is_cg:
                    detected_lang = "cg"
                elif has_devanagari:
                    detected_lang = "hi-IN"
                else:
                    detected_lang = data.get("language_code", "en-IN")

            if not user_text:
                continue

            # Step B: Layer 1 Input Guardrail Inspection
            guardrail_res = guardrails.validate_input(user_text)

            await websocket.send_json({
                "type": "guardrail_status",
                "stage": "input",
                "is_safe": guardrail_res.is_safe,
                "threat_level": guardrail_res.threat_level,
                "owasp_category": guardrail_res.owasp_category,
                "violation_type": guardrail_res.violation_type,
                "pii_redacted": guardrail_res.pii_redacted,
                "flags": guardrail_res.flags,
                "latency_ms": guardrail_res.latency_ms,
                "reason": guardrail_res.reason
            })

            # If Input Guardrail detects an adversarial attack / violation:
            if not guardrail_res.is_safe:
                refusal_text = f"Security Notice: {guardrail_res.reason or 'I cannot process that request due to safety policies.'}"
                
                # Audit log to database
                db = SessionLocal()
                try:
                    audit = GuardrailAudit(
                        session_id=session_id,
                        input_text=user_text,
                        violation_type=guardrail_res.violation_type or "injection",
                        flagged_terms=", ".join(guardrail_res.flags),
                        action_taken="blocked"
                    )
                    db.add(audit)
                    db.commit()
                finally:
                    db.close()

                # Synthesize safe refusal audio
                refusal_audio = await tts_service.synthesize_speech(refusal_text, detected_lang)
                await websocket.send_json({
                    "type": "guardrail_refusal",
                    "text": refusal_text,
                    "threat_level": guardrail_res.threat_level,
                    "owasp_category": guardrail_res.owasp_category,
                    "violation_type": guardrail_res.violation_type,
                    "flags": guardrail_res.flags,
                    "latency_ms": guardrail_res.latency_ms,
                    "audio_base64": base64.b64encode(refusal_audio).decode("utf-8") if refusal_audio else ""
                })
                continue

            # Step C: Retrieve Context Memory
            sanitized_input = guardrail_res.sanitized_text
            chat_history = await memory_manager.get_gemini_history(session_id)

            # Step D: Stream from Gemini Flash
            token_gen = llm_service.stream_response(
                user_query=sanitized_input,
                chat_history=chat_history,
                detected_lang=detected_lang
            )

            # Step E: Sentence-Level Chunking & Real-time TTS
            full_assistant_response = ""
            chunk_index = 0
            first_audio_sent = False
            first_audio_latency = 0

            async for sentence in stream_chunker.chunk_stream(token_gen):
                # Layer 2: Output Guardrail inspection & voice formatting
                output_guard_res = guardrails.validate_output(sentence)
                safe_sentence = output_guard_res.sanitized_text
                if not safe_sentence:
                    continue

                full_assistant_response += " " + safe_sentence
                chunk_index += 1

                # Send text token/sentence to client
                await websocket.send_json({
                    "type": "llm_chunk",
                    "chunk_index": chunk_index,
                    "text": safe_sentence
                })

                # Synthesize speech for this sentence
                sentence_audio = await tts_service.synthesize_speech(safe_sentence, detected_lang)
                
                if not first_audio_sent:
                    first_audio_sent = True
                    first_audio_latency = int((time.time() - start_time) * 1000)

                await websocket.send_json({
                    "type": "audio_chunk",
                    "chunk_index": chunk_index,
                    "audio_base64": base64.b64encode(sentence_audio).decode("utf-8") if sentence_audio else "",
                    "ttfa_latency_ms": first_audio_latency
                })

            # Step F: Persist to Memory Store & DB
            clean_full_response = full_assistant_response.strip()
            total_time_ms = int((time.time() - start_time) * 1000)

            await memory_manager.append_turn(
                session_id=session_id,
                user_text=sanitized_input,
                assistant_text=clean_full_response,
                detected_lang=detected_lang,
                latency_ms=first_audio_latency or total_time_ms
            )

            await websocket.send_json({
                "type": "turn_complete",
                "user_text": sanitized_input,
                "assistant_text": clean_full_response,
                "detected_language": detected_lang,
                "ttfa_latency_ms": first_audio_latency,
                "total_duration_ms": total_time_ms
            })

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket processing error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
