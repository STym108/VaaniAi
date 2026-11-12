import React, { useRef, useState } from 'react'
import { Header } from './components/Header'
import { VoiceOrb } from './components/VoiceOrb'
import { AudioVisualizer } from './components/AudioVisualizer'
import { ChatStream } from './components/ChatStream'
import { QuickPromptTray } from './components/QuickPromptTray'
import { GuardrailInspector } from './components/GuardrailInspector'
import { SettingsModal } from './components/SettingsModal'
import { AudioRecorder, type AudioRecorderResult } from './services/audioRecorder'
import { processVoiceQuery } from './services/mockVoiceEngine'
import { useVoiceStore } from './store/useVoiceStore'
import { Send, Sparkles, MessageSquare } from 'lucide-react'
import { wsClient } from './services/websocketClient'

export const App: React.FC = () => {
  const { isRecording, setRecording, setLiveVolume, activeMode, addMessage, setProcessing } = useVoiceStore()
  const [textInput, setTextInput] = useState('')
  const recorderRef = useRef<AudioRecorder | null>(null)

  // Auto connect to WebSocket on mount
  React.useEffect(() => {
    wsClient.connect()
    return () => {
      wsClient.disconnect()
    }
  }, [])

  // Initialize or toggle audio recording
  const handleToggleRecord = async () => {
    if (isRecording) {
      // Stop recording
      setRecording(false)
      let recordResult: AudioRecorderResult | null = null
      
      if (recorderRef.current) {
        recordResult = await recorderRef.current.stop()
      }

      const spokenText = recordResult?.transcript?.trim() || ''

      if (activeMode === 'live' && recordResult?.blob && recordResult.blob.size > 100) {
        // In Live Mode: ALWAYS send authentic speech audio to Sarvam Saaras AI STT on backend!
        // Sarvam Saaras accurately auto-detects English, Hindi, and Chhattisgarhi without Devanagari transliteration glitches.
        setProcessing(true)
        const reader = new FileReader()
        reader.onloadend = () => {
          const base64Audio = (reader.result as string).split(',')[1]
          if (base64Audio) {
            wsClient.sendAudioBase64(base64Audio)
          }
        }
        reader.readAsDataURL(recordResult.blob)
      } else if (spokenText) {
        // Fallback for Demo mode
        processVoiceQuery(spokenText)
      } else {
        // Prompt user to speak again if no speech detected
        alert('No clear speech detected. Please tap the mic, speak your question, and tap again!')
      }
    } else {
      // Start recording
      try {
        if (!recorderRef.current) {
          recorderRef.current = new AudioRecorder((vol) => {
            setLiveVolume(vol)
          })
        }
        await recorderRef.current.start()
        setRecording(true)
      } catch (err) {
        console.error('Microphone permission or error:', err)
        alert('Please allow microphone permissions in your browser to test voice input.')
      }
    }
  }

  const handleSendText = (e: React.FormEvent) => {
    e.preventDefault()
    if (!textInput.trim()) return
    const query = textInput.trim()
    setTextInput('')

    const hasDevanagari = /[\u0900-\u097F]/.test(query)
    const isCG = /काबर|कइसे|कतेक|तोर|मोर|हमन|तुमन|बर|ला|नइ|झन|हे|हव|करथें|होइस|कतका|लागथे|आथे|जाथे/.test(query)
    const langCode = isCG ? 'cg' : hasDevanagari ? 'hi-IN' : 'en-IN'
    const langLabel = isCG ? '🌾 Chhattisgarhi' : hasDevanagari ? '🇮🇳 Hindi' : '🇬🇧 English'

    if (activeMode === 'live') {
      addMessage({
        role: 'user',
        text: query,
        languageLabel: langLabel
      })
      setProcessing(true)
      wsClient.sendText(query, langCode)
    } else {
      processVoiceQuery(query)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#0A0C0E] text-[#ECE6DD] ambient-mesh">
      {/* Top Navigation Bar */}
      <Header />

      {/* Main Interactive Stage */}
      <main className="flex-1 max-w-7xl w-full mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 p-4 md:p-6 overflow-hidden">
        {/* Left Column: Voice Orb & Live Visualizer (Hero Area) */}
        <section className="lg:col-span-5 flex flex-col justify-between glass-panel rounded-3xl p-6 relative overflow-hidden shadow-2xl">
          {/* Subtle Ambient Background Watermark */}
          <div className="absolute top-4 right-4 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/5 border border-white/5 text-[11px] text-[#A8A398]">
            <Sparkles className="w-3.5 h-3.5 text-[#DFB15B]" />
            <span>Real-time Stream Engine</span>
          </div>

          <div className="my-auto flex flex-col items-center">
            {/* Central Animated Fluid Orb */}
            <VoiceOrb onToggleRecord={handleToggleRecord} />

            {/* Live Audio Frequency Spectrum Canvas */}
            <AudioVisualizer />
          </div>

          {/* Quick Informational Pill */}
          <div className="pt-4 border-t border-white/5 text-center text-xs text-[#8A857C]">
            <span className="font-mono text-[#DFB15B]">Auto-detects</span> Hindi, English &amp; Hinglish with Sub-Second Audio Streaming
          </div>
        </section>

        {/* Right Column: Multi-Turn Conversation Log & Text Bar */}
        <section className="lg:col-span-7 flex flex-col glass-panel rounded-3xl overflow-hidden shadow-2xl">
          {/* Conversation Feed Header */}
          <div className="px-5 py-3.5 border-b border-white/5 bg-[#12161A]/80 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-[#DFB15B]" />
              <h2 className="text-xs font-semibold uppercase tracking-wider text-[#C5C0B6]">
                Live Multilingual Conversation Log
              </h2>
            </div>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#689F77]/15 text-[#88C498] border border-[#689F77]/30">
              Context Window Active
            </span>
          </div>

          {/* Chat Stream History */}
          <ChatStream />

          {/* Quick Scenario Buttons for Presentation */}
          <QuickPromptTray />

          {/* Bottom Text Fallback Input */}
          <form
            onSubmit={handleSendText}
            className="p-3 border-t border-white/5 bg-[#101418] flex items-center gap-2"
          >
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Or type your query in Hindi, English, or Hinglish..."
              className="flex-1 bg-[#181D22] border border-white/10 rounded-xl px-4 py-2.5 text-xs text-[#ECE6DD] placeholder-[#7A766F] focus:outline-none focus:border-[#DFB15B]/50 transition-colors"
            />
            <button
              type="submit"
              disabled={!textInput.trim()}
              className="p-2.5 rounded-xl bg-gradient-to-r from-[#DFB15B] to-[#C88A48] text-[#0A0C0E] disabled:opacity-40 disabled:cursor-not-allowed hover:brightness-110 transition-all cursor-pointer"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </section>
      </main>

      {/* Floating Drawers & Modals */}
      <GuardrailInspector />
      <SettingsModal />
    </div>
  )
}

export default App
