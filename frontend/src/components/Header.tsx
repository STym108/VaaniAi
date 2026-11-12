import React from 'react'
import { ShieldCheck, Settings, RotateCcw, Sparkles, Square } from 'lucide-react'
import { useVoiceStore } from '../store/useVoiceStore'
import { wsClient } from '../services/websocketClient'

export const Header: React.FC = () => {
  const {
    guardrailSummary,
    clearHistory,
    setInspectorOpen,
    setSettingsOpen,
    isSpeaking,
    isRecording,
  } = useVoiceStore()

  return (
    <header className="w-full px-6 py-3.5 glass-panel border-b border-white/5 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Identity */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#C88A48] via-[#DFB15B] to-[#F3CA78] flex items-center justify-center shadow-md shadow-[#DFB15B]/20 ring-1 ring-[#DFB15B]/40">
            <Sparkles className="w-4 h-4 text-[#0A0C0E]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold tracking-tight text-[#ECE6DD] font-heading">
                Vani AI
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-[#DFB15B]/15 text-[#E6BA6E] border border-[#DFB15B]/25">
                Multilingual Voice AI
              </span>
            </div>
            <p className="text-[11px] text-[#8A857C] font-sans">
              Hindi &bull; English &bull; Chhattisgarhi
            </p>
          </div>
        </div>

        {/* Center Indicators & Stop Speaking Action */}
        <div className="flex items-center gap-3">
          {/* Prominent Stop Button when Assistant is Speaking */}
          {isSpeaking && (
            <button
              onClick={() => wsClient.stopSpeaking()}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 hover:text-red-200 text-xs font-medium transition-all shadow-lg shadow-red-500/10 cursor-pointer animate-pulse"
              title="Stop voice playback immediately"
            >
              <Square className="w-3 h-3 fill-current" />
              <span>Stop Speaking</span>
            </button>
          )}

          {/* Guardrail Status Badge */}
          <button
            onClick={() => setInspectorOpen(true)}
            className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#14181C]/90 border border-[#689F77]/30 hover:border-[#689F77]/60 text-xs text-[#C5C0B6] transition-all cursor-pointer group"
            title="Open Guardrail Security Inspector"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-[#689F77] group-hover:scale-110 transition-transform" />
            <span className="text-[#9B978F]">Guardrails:</span>
            <span className="font-semibold text-[#689F77]">
              {guardrailSummary.blockedPrompts > 0
                ? `${guardrailSummary.blockedPrompts} Blocked`
                : 'Protected'}
            </span>
          </button>

          {/* Live Status Pill */}
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#14181C]/90 border border-white/5 text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                isRecording
                  ? 'bg-[#D97D54] animate-ping'
                  : isSpeaking
                  ? 'bg-[#DFB15B] animate-pulse'
                  : 'bg-[#689F77]'
              }`}
            />
            <span className="text-[#9B978F]">
              {isRecording ? 'Listening...' : isSpeaking ? 'Speaking...' : 'Ready'}
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setInspectorOpen(true)}
            className="p-2 rounded-lg bg-[#181D22] hover:bg-[#20272E] text-[#B8B3A8] hover:text-[#ECE6DD] border border-white/5 transition-colors cursor-pointer"
            title="Inspect Guardrails & Security Policies"
          >
            <ShieldCheck className="w-4 h-4 text-[#689F77]" />
          </button>

          <button
            onClick={clearHistory}
            className="p-2 rounded-lg bg-[#181D22] hover:bg-[#20272E] text-[#B8B3A8] hover:text-[#ECE6DD] border border-white/5 transition-colors cursor-pointer"
            title="Clear Chat History"
          >
            <RotateCcw className="w-4 h-4" />
          </button>

          <button
            onClick={() => setSettingsOpen(true)}
            className="p-2 rounded-lg bg-[#181D22] hover:bg-[#20272E] text-[#B8B3A8] hover:text-[#ECE6DD] border border-white/5 transition-colors cursor-pointer"
            title="System Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  )
}
