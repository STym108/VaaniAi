import { create } from 'zustand'

export interface GuardrailMetadata {
  inputPassed: boolean
  outputPassed: boolean
  piiRedacted: boolean
  toxicityScore: number
  flags: string[]
  reason?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  text: string
  language?: string
  languageLabel?: string
  timestamp: string
  audioUrl?: string
  latencyMs?: number
  guardrailStatus?: GuardrailMetadata
  isStreaming?: boolean
}

interface VoiceStoreState {
  messages: ChatMessage[]
  isRecording: boolean
  isProcessing: boolean
  isSpeaking: boolean
  liveVolume: number
  currentLanguage: string
  activeMode: 'demo' | 'live'
  latencyStats: {
    lastTTFA: number
    averageTTFA: number
    totalTurns: number
  }
  guardrailSummary: {
    totalScanned: number
    blockedPrompts: number
    piiMaskedCount: number
  }
  isInspectorOpen: boolean
  isSettingsOpen: boolean

  // Actions
  addMessage: (msg: Omit<ChatMessage, 'id' | 'timestamp'> & { id?: string }) => void
  updateStreamingMessage: (id: string, textChunk: string) => void
  setRecording: (val: boolean) => void
  setProcessing: (val: boolean) => void
  setSpeaking: (val: boolean) => void
  setLiveVolume: (val: number) => void
  setCurrentLanguage: (lang: string) => void
  setActiveMode: (mode: 'demo' | 'live') => void
  setInspectorOpen: (open: boolean) => void
  setSettingsOpen: (open: boolean) => void
  updateLatency: (ttfa: number) => void
  recordGuardrailEvent: (blocked: boolean, pii: boolean) => void
  clearHistory: () => void
}

export const useVoiceStore = create<VoiceStoreState>((set) => ({
  messages: [
    {
      id: 'welcome-msg',
      role: 'assistant',
      text: 'Namaste! I am Vani AI, your voice assistant. You can speak to me naturally in Hindi, English, or Hinglish. I will auto-detect your language and respond in real-time with verified guardrails.',
      language: 'en-IN',
      languageLabel: '🇮🇳 Multilingual Ready',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      latencyMs: 620,
      guardrailStatus: {
        inputPassed: true,
        outputPassed: true,
        piiRedacted: false,
        toxicityScore: 0.01,
        flags: ['System Welcome Initialized'],
      },
    },
  ],
  isRecording: false,
  isProcessing: false,
  isSpeaking: false,
  liveVolume: 0,
  currentLanguage: 'Auto (Indic & Global)',
  activeMode: 'live',
  latencyStats: {
    lastTTFA: 680,
    averageTTFA: 710,
    totalTurns: 1,
  },
  guardrailSummary: {
    totalScanned: 1,
    blockedPrompts: 0,
    piiMaskedCount: 0,
  },
  isInspectorOpen: false,
  isSettingsOpen: false,

  addMessage: (msg) =>
    set((state) => {
      const newMsg: ChatMessage = {
        id: msg.id || 'msg-' + Math.random().toString(36).substring(2, 9),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        ...msg,
      }
      return { messages: [...state.messages, newMsg] }
    }),

  updateStreamingMessage: (id, textChunk) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, text: m.text + textChunk, isStreaming: true } : m
      ),
    })),

  setRecording: (val) => set({ isRecording: val }),
  setProcessing: (val) => set({ isProcessing: val }),
  setSpeaking: (val) => set({ isSpeaking: val }),
  setLiveVolume: (val) => set({ liveVolume: val }),
  setCurrentLanguage: (lang) => set({ currentLanguage: lang }),
  setActiveMode: (mode) => set({ activeMode: mode }),
  setInspectorOpen: (open) => set({ isInspectorOpen: open }),
  setSettingsOpen: (open) => set({ isSettingsOpen: open }),

  updateLatency: (ttfa) =>
    set((state) => {
      const newTotal = state.latencyStats.totalTurns + 1
      const newAvg = Math.round(
        (state.latencyStats.averageTTFA * state.latencyStats.totalTurns + ttfa) / newTotal
      )
      return {
        latencyStats: {
          lastTTFA: ttfa,
          averageTTFA: newAvg,
          totalTurns: newTotal,
        },
      }
    }),

  recordGuardrailEvent: (blocked, pii) =>
    set((state) => ({
      guardrailSummary: {
        totalScanned: state.guardrailSummary.totalScanned + 1,
        blockedPrompts: state.guardrailSummary.blockedPrompts + (blocked ? 1 : 0),
        piiMaskedCount: state.guardrailSummary.piiMaskedCount + (pii ? 1 : 0),
      },
    })),

  clearHistory: () =>
    set({
      messages: [],
      latencyStats: { lastTTFA: 0, averageTTFA: 0, totalTurns: 0 },
    }),
}))
