import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, MicOff, Volume2, Sparkles, Loader2, Square } from 'lucide-react'
import { useVoiceStore } from '../store/useVoiceStore'
import { wsClient } from '../services/websocketClient'

interface VoiceOrbProps {
  onToggleRecord: () => void
}

export const VoiceOrb: React.FC<VoiceOrbProps> = ({ onToggleRecord }) => {
  const { isRecording, isProcessing, isSpeaking, liveVolume } = useVoiceStore()

  // Dynamic scale calculated from audio amplitude
  const dynamicScale = isRecording ? 1 + liveVolume * 0.45 : isSpeaking ? 1.08 : 1

  return (
    <div className="flex flex-col items-center justify-center relative py-8 select-none">
      {/* Ambient Radial Halo */}
      <div className="absolute w-72 h-72 rounded-full bg-radial from-[#DFB15B]/15 via-[#C88A48]/5 to-transparent blur-3xl pointer-events-none -z-10" />

      {/* Outer Pulsing Waves when Recording */}
      <AnimatePresence>
        {isRecording && (
          <>
            <motion.div
              initial={{ scale: 0.9, opacity: 0.8 }}
              animate={{ scale: [1, 1.45, 1.8], opacity: [0.6, 0.3, 0] }}
              transition={{ duration: 2.2, repeat: Infinity, ease: 'easeOut' }}
              className="absolute w-44 h-44 rounded-full border border-[#DFB15B]/40 pointer-events-none"
            />
            <motion.div
              initial={{ scale: 0.9, opacity: 0.6 }}
              animate={{ scale: [1, 1.35, 1.6], opacity: [0.5, 0.2, 0] }}
              transition={{ duration: 2.2, delay: 0.7, repeat: Infinity, ease: 'easeOut' }}
              className="absolute w-44 h-44 rounded-full border border-[#D98852]/30 pointer-events-none"
            />
          </>
        )}
      </AnimatePresence>

      {/* Main Interactive Animated Orb */}
      <motion.button
        onClick={onToggleRecord}
        animate={{ scale: dynamicScale }}
        transition={{ type: 'spring', stiffness: 260, damping: 20 }}
        className={`relative w-36 h-36 rounded-full flex items-center justify-center cursor-pointer transition-all duration-500 focus:outline-none ${
          isRecording
            ? 'bg-gradient-to-br from-[#D97D54] via-[#C88A48] to-[#DFB15B] shadow-2xl shadow-[#D97D54]/40 ring-4 ring-[#D97D54]/50'
            : isSpeaking
            ? 'bg-gradient-to-br from-[#DFB15B] via-[#E2B768] to-[#689F77] shadow-2xl shadow-[#DFB15B]/40 ring-4 ring-[#DFB15B]/50'
            : isProcessing
            ? 'bg-gradient-to-br from-[#20272E] via-[#2A333D] to-[#181D22] ring-2 ring-[#DFB15B]/30'
            : 'bg-gradient-to-br from-[#181D22] via-[#222930] to-[#14181C] hover:from-[#222930] hover:to-[#181D22] ring-1 ring-white/10 hover:ring-[#DFB15B]/50 shadow-xl'
        }`}
      >
        {/* Inner Glass Sheen */}
        <div className="absolute inset-1.5 rounded-full bg-black/25 backdrop-blur-sm flex items-center justify-center">
          {isProcessing ? (
            <Loader2 className="w-12 h-12 text-[#DFB15B] animate-spin" />
          ) : isRecording ? (
            <motion.div
              animate={{ scale: [1, 1.15, 1] }}
              transition={{ duration: 1.2, repeat: Infinity }}
            >
              <MicOff className="w-12 h-12 text-[#FFF7ED]" />
            </motion.div>
          ) : isSpeaking ? (
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1.4, repeat: Infinity }}
            >
              <Volume2 className="w-12 h-12 text-[#0A0C0E]" />
            </motion.div>
          ) : (
            <div className="relative group">
              <Mic className="w-12 h-12 text-[#DFB15B] group-hover:scale-110 transition-transform duration-300" />
              <Sparkles className="w-4 h-4 text-[#F3CA78] absolute -top-1 -right-1 animate-pulse" />
            </div>
          )}
        </div>

        {/* Dynamic Voice Level Ring */}
        {isRecording && (
          <svg className="absolute inset-0 w-full h-full -rotate-90 pointer-events-none">
            <circle
              cx="72"
              cy="72"
              r="68"
              fill="none"
              stroke="#FFF"
              strokeWidth="3"
              strokeDasharray="427"
              strokeDashoffset={427 - 427 * liveVolume}
              className="opacity-70 transition-all duration-75"
            />
          </svg>
        )}
      </motion.button>

      {/* Status Label & Instructions */}
      <div className="mt-5 text-center flex flex-col items-center">
        <p className="text-sm font-medium text-[#ECE6DD]">
          {isRecording
            ? 'Listening... (Tap to Send)'
            : isProcessing
            ? 'Thinking...'
            : isSpeaking
            ? 'Speaking...'
            : 'Tap microphone to speak'}
        </p>
        <p className="text-xs text-[#8A857C] mt-1">
          Hindi &bull; English &bull; Chhattisgarhi
        </p>

        {/* Dedicated Stop Speaking Button */}
        {isSpeaking && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              wsClient.stopSpeaking()
            }}
            className="mt-3 flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/20 hover:bg-red-500/30 border border-red-500/40 text-red-300 hover:text-red-200 text-xs font-semibold tracking-wide transition-all shadow-lg shadow-red-500/10 cursor-pointer animate-pulse"
            title="Stop voice playback"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
            <span>Stop Speaking</span>
          </button>
        )}
      </div>
    </div>
  )
}
