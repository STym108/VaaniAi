import React, { useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Volume2, Square, ShieldCheck, AlertTriangle, User, Bot } from 'lucide-react'
import { useVoiceStore, type ChatMessage } from '../store/useVoiceStore'
import { wsClient } from '../services/websocketClient'

export const ChatStream: React.FC = () => {
  const { messages, isSpeaking } = useVoiceStore()
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleReplay = (text: string, lang?: string) => {
    wsClient.stopSpeaking()
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = lang?.startsWith('hi') ? 'hi-IN' : 'en-US'
      utterance.rate = 1.02
      utterance.onstart = () => {
        useVoiceStore.getState().setSpeaking(true)
      }
      utterance.onend = () => {
        useVoiceStore.getState().setSpeaking(false)
      }
      utterance.onerror = () => {
        useVoiceStore.getState().setSpeaking(false)
      }
      window.speechSynthesis.speak(utterance)
    }
  }

  return (
    <div className="w-full flex-1 overflow-y-auto px-4 py-6 space-y-5">
      <AnimatePresence initial={false}>
        {messages.map((msg: ChatMessage) => {
          const isUser = msg.role === 'user'
          const isViolation =
            msg.guardrailStatus && !msg.guardrailStatus.inputPassed

          return (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 16, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.3 }}
              className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {/* Assistant Icon */}
              {!isUser && (
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#C88A48] to-[#DFB15B] flex-shrink-0 flex items-center justify-center text-[#0A0C0E] shadow-md shadow-[#DFB15B]/10 ring-1 ring-[#DFB15B]/30">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              {/* Message Content Bubble */}
              <div
                className={`max-w-[82%] md:max-w-[70%] rounded-2xl p-4.5 transition-all ${
                  isUser
                    ? 'bg-[#1C2228] border border-white/10 text-[#ECE6DD] rounded-tr-sm'
                    : isViolation
                    ? 'bg-[#2A1815] border border-[#D97D54]/40 text-[#FCEEEA] rounded-tl-sm'
                    : 'glass-panel text-[#ECE6DD] rounded-tl-sm ring-1 ring-white/5'
                }`}
              >
                {/* Header Meta: Language & Guardrail Badges */}
                <div className="flex flex-wrap items-center gap-2 mb-2 pb-2 border-b border-white/5 text-[11px]">
                  {/* Language Tag */}
                  {msg.languageLabel && (
                    <span className="px-2 py-0.5 rounded-md bg-[#DFB15B]/10 text-[#E6BA6E] font-medium border border-[#DFB15B]/20">
                      {msg.languageLabel}
                    </span>
                  )}

                  {/* Guardrail Safety Status */}
                  {msg.guardrailStatus && (
                    <span
                      className={`flex items-center gap-1 px-2 py-0.5 rounded-md font-medium ${
                        isViolation
                          ? 'bg-[#D97D54]/20 text-[#FFA88B] border border-[#D97D54]/30'
                          : 'bg-[#689F77]/15 text-[#88C498] border border-[#689F77]/25'
                      }`}
                    >
                      {isViolation ? (
                        <AlertTriangle className="w-3 h-3" />
                      ) : (
                        <ShieldCheck className="w-3 h-3" />
                      )}
                      {isViolation
                        ? 'Guardrail Interception'
                        : msg.guardrailStatus.piiRedacted
                        ? 'PII Masked'
                        : 'Guardrail Passed'}
                    </span>
                  )}
                </div>

                {/* Main Text Message */}
                <p className="text-[14px] leading-relaxed whitespace-pre-wrap font-sans">
                  {msg.text}
                </p>

                {/* Footer Controls: Audio Replay / Stop for Assistant */}
                {!isUser && (
                  <div className="flex items-center justify-between mt-3 pt-2 border-t border-white/5 text-xs text-[#8A857C]">
                    <div className="flex items-center gap-2">
                      {isSpeaking ? (
                        <button
                          onClick={() => wsClient.stopSpeaking()}
                          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 font-medium transition-colors cursor-pointer"
                        >
                          <Square className="w-3 h-3 fill-current" />
                          <span>Stop Voice</span>
                        </button>
                      ) : (
                        <button
                          onClick={() => handleReplay(msg.text, msg.language)}
                          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/5 hover:bg-white/10 text-[#DFB15B] hover:text-[#F3CA78] transition-colors cursor-pointer"
                        >
                          <Volume2 className="w-3.5 h-3.5" />
                          <span>Replay</span>
                        </button>
                      )}
                    </div>
                    <span className="text-[11px] font-mono text-[#6E6A62]">
                      {msg.timestamp}
                    </span>
                  </div>
                )}
              </div>

              {/* User Avatar */}
              {isUser && (
                <div className="w-9 h-9 rounded-xl bg-[#2A333C] border border-white/10 flex-shrink-0 flex items-center justify-center text-[#DFB15B]">
                  <User className="w-4 h-4" />
                </div>
              )}
            </motion.div>
          )
        })}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  )
}
