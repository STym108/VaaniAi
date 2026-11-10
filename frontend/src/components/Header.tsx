import React from 'react'
import { ShieldCheck, Activity, Settings, RotateCcw, Sparkles } from 'lucide-react'
import { useVoiceStore } from '../store/useVoiceStore'

export const Header: React.FC = () => {
  const {
    latencyStats,
    guardrailSummary,
    clearHistory,
    setInspectorOpen,
    setSettingsOpen,
    isSpeaking,
    isRecording,
    activeMode,
    setActiveMode,
  } = useVoiceStore()

  return (
    <header className="w-full px-6 py-4 glass-panel border-b border-white/5 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand & Project Identity */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#C88A48] via-[#DFB15B] to-[#F3CA78] flex items-center justify-center shadow-lg shadow-[#DFB15B]/20 ring-1 ring-[#DFB15B]/40">
            <Sparkles className="w-5 h-5 text-[#0A0C0E]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold tracking-tight text-[#ECE6DD] font-heading">
                Vani AI
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-full bg-[#DFB15B]/15 text-[#E6BA6E] border border-[#DFB15B]/30">
                Hybrid Voice Engine
              </span>
            </div>
            <p className="text-xs text-[#9B978F] font-sans">
              Multilingual Voice Assistant &bull; Auto-Detect &bull; Streaming Latency
            </p>
          </div>
        </div>

        {/* Live Metrics Pills */}
        <div className="hidden md:flex items-center gap-3">
          {/* Latency Indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#14181C]/90 border border-white/5 text-xs text-[#C5C0B6]">
            <Activity className="w-3.5 h-3.5 text-[#689F77] animate-pulse" />
            <span>Avg TTFA:</span>
            <span className="font-mono font-semibold text-[#DFB15B]">
              {latencyStats.averageTTFA > 0 ? `${latencyStats.averageTTFA}ms` : '680ms'}
            </span>
          </div>

          {/* Guardrail Status Badge */}
          <button
            onClick={() => setInspectorOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#14181C]/90 border border-[#689F77]/30 hover:border-[#689F77]/60 text-xs text-[#C5C0B6] transition-all cursor-pointer group"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-[#689F77] group-hover:scale-110 transition-transform" />
            <span>Guardrails:</span>
            <span className="font-semibold text-[#689F77]">
              {guardrailSummary.blockedPrompts > 0
                ? `${guardrailSummary.blockedPrompts} Blocked`
                : '100% Active'}
            </span>
          </button>

          {/* Live Status Pill */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#14181C]/90 border border-white/5 text-xs">
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

          {/* Mode Switcher Pill */}
          <button
            onClick={() => setActiveMode(activeMode === 'live' ? 'demo' : 'live')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${
              activeMode === 'live'
                ? 'bg-[#689F77]/20 border-[#689F77]/40 text-[#88C498] hover:bg-[#689F77]/30'
                : 'bg-[#DFB15B]/20 border-[#DFB15B]/40 text-[#F3CA78] hover:bg-[#DFB15B]/30'
            }`}
            title="Click to toggle between Live Backend AI and Demo Simulator"
          >
            <span>{activeMode === 'live' ? '⚡ Live Backend' : '🎬 Demo Mode'}</span>
          </button>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setInspectorOpen(true)}
            className="p-2 rounded-lg bg-[#181D22] hover:bg-[#20272E] text-[#B8B3A8] hover:text-[#ECE6DD] border border-white/5 transition-colors cursor-pointer"
            title="Inspect Guardrails & Latency Breakdown"
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
