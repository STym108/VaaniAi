import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Sliders, Volume2, Shield, Radio, Check } from 'lucide-react'
import { useVoiceStore } from '../store/useVoiceStore'

export const SettingsModal: React.FC = () => {
  const { isSettingsOpen, setSettingsOpen, activeMode, setActiveMode } = useVoiceStore()

  if (!isSettingsOpen) return null

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
        {/* Backdrop click to close */}
        <div className="fixed inset-0" onClick={() => setSettingsOpen(false)} />

        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="relative w-full max-w-md bg-[#13171B] border border-white/10 rounded-2xl p-6 shadow-2xl z-10 space-y-5"
        >
          {/* Header */}
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <Sliders className="w-5 h-5 text-[#DFB15B]" />
              <h2 className="text-base font-bold text-[#ECE6DD] font-heading">
                System Configurations
              </h2>
            </div>
            <button
              onClick={() => setSettingsOpen(false)}
              className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-[#9B978F] hover:text-[#ECE6DD]"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Mode Switcher */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-[#DFB15B] flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5" />
              <span>Execution Pipeline Mode</span>
            </label>
            <div className="grid grid-cols-2 gap-2.5">
              <button
                onClick={() => setActiveMode('demo')}
                className={`p-3 rounded-xl border text-left cursor-pointer transition-all ${
                  activeMode === 'demo'
                    ? 'bg-[#DFB15B]/15 border-[#DFB15B]/50 text-[#F3CA78]'
                    : 'bg-[#181D22] border-white/5 text-[#9B978F] hover:border-white/20'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold">Interactive Demo</span>
                  {activeMode === 'demo' && <Check className="w-3.5 h-3.5" />}
                </div>
                <p className="text-[10px] text-[#A8A398]">
                  Full offline simulation ready for teacher presentation.
                </p>
              </button>

              <button
                onClick={() => setActiveMode('live')}
                className={`p-3 rounded-xl border text-left cursor-pointer transition-all ${
                  activeMode === 'live'
                    ? 'bg-[#689F77]/15 border-[#689F77]/50 text-[#88C498]'
                    : 'bg-[#181D22] border-white/5 text-[#9B978F] hover:border-white/20'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold">Live WebSocket</span>
                  {activeMode === 'live' && <Check className="w-3.5 h-3.5" />}
                </div>
                <p className="text-[10px] text-[#A8A398]">
                  Connects to FastAPI server (/ws/converse).
                </p>
              </button>
            </div>
          </div>

          {/* Guardrails Configuration */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-[#DFB15B] flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5" />
              <span>Guardrail Strictness</span>
            </label>
            <div className="p-3 rounded-xl bg-[#181D22] border border-white/5 flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-[#ECE6DD] block">
                  Prompt Injection &amp; PII Shield
                </span>
                <span className="text-[10px] text-[#8A857C]">
                  Strict filtering active on both Ingress &amp; Egress
                </span>
              </div>
              <span className="px-2 py-0.5 rounded bg-[#689F77]/20 text-[#88C498] text-[10px] font-mono">
                ENFORCED
              </span>
            </div>
          </div>

          {/* Voice Output Configuration */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-[#DFB15B] flex items-center gap-1.5">
              <Volume2 className="w-3.5 h-3.5" />
              <span>Neural Voice Engine</span>
            </label>
            <div className="p-3 rounded-xl bg-[#181D22] border border-white/5 flex items-center justify-between text-xs text-[#C5C0B6]">
              <span>Primary Engine:</span>
              <span className="font-mono text-[#DFB15B]">Sarvam Bulbul (Neural Indic)</span>
            </div>
          </div>

          {/* Done Button */}
          <button
            onClick={() => setSettingsOpen(false)}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-[#DFB15B] to-[#C88A48] text-[#0A0C0E] font-semibold text-xs tracking-wide hover:brightness-110 transition-all cursor-pointer shadow-lg shadow-[#DFB15B]/20"
          >
            Save &amp; Close
          </button>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
