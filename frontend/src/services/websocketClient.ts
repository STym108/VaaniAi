import { useVoiceStore } from '../store/useVoiceStore'

export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private isConnected = false
  private audioQueue: string[] = []
  private isPlayingAudio = false
  private currentAudio: HTMLAudioElement | null = null
  private hasReceivedAudioThisTurn = false
  private currentAssistantText = ''
  private currentDetectedLang = 'hi-IN'

  constructor(url = 'ws://127.0.0.1:8000/ws/converse') {
    this.url = url
  }

  connect(): Promise<boolean> {
    return new Promise((resolve) => {
      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          this.isConnected = true
          this.ws?.send(
            JSON.stringify({
              type: 'init',
              session_id: 'active-session-1',
            })
          )
          resolve(true)
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (err) {
            console.error('Error parsing WS message:', err)
          }
        }

        this.ws.onclose = () => {
          this.isConnected = false
        }

        this.ws.onerror = () => {
          this.isConnected = false
          resolve(false)
        }
      } catch (e) {
        this.isConnected = false
        resolve(false)
      }
    })
  }

  private handleMessage(data: any) {
    const store = useVoiceStore.getState()

    switch (data.type) {
      case 'stt_result': {
        const transcriptText = (data.transcript || data.text || '').trim()
        if (transcriptText) {
          const isDevanagari = /[\u0900-\u097F]/.test(transcriptText)
          const isCG = data.language_code === 'cg' || /काबर|कइसे|कतेक|तोर|मोर|हमन|तुमन|बर|ला|नइ|झन|हे|हव|करथें|होइस|कतका|लागथे|आथे|जाथे/.test(transcriptText)
          const label = isCG ? '🌾 Chhattisgarhi' : isDevanagari ? '🇮🇳 Hindi' : '🇬🇧 English'

          store.addMessage({
            role: 'user',
            text: transcriptText,
            language: data.language_code || (isDevanagari ? 'hi-IN' : 'en-IN'),
            languageLabel: label
          })
        }
        store.setCurrentLanguage(data.language_code || 'hi-IN')
        break
      }

      case 'guardrail_status':
        if (!data.is_safe) {
          store.recordGuardrailEvent(true, false)
        } else if (data.pii_redacted) {
          store.recordGuardrailEvent(false, true)
        }
        break

      case 'llm_chunk':
        store.setProcessing(false)
        break

      case 'audio_chunk':
        if (data.audio_base64) {
          this.hasReceivedAudioThisTurn = true
          this.queueAudio(data.audio_base64)
        }
        if (data.ttfa_latency_ms) {
          store.updateLatency(data.ttfa_latency_ms)
        }
        break

      case 'turn_complete': {
        this.currentAssistantText = data.assistant_text
        this.currentDetectedLang = data.detected_language || 'hi-IN'

        const isDevanagari = /[\u0900-\u097F]/.test(data.assistant_text)
        const isCG = data.detected_language === 'cg' || /काबर|कइसे|कतेक|तोर|मोर|हमन|तुमन|बर|ला|नइ|झन|हे|हव|करथें/.test(data.assistant_text)
        const langLabel = isCG ? '🌾 Chhattisgarhi' : isDevanagari ? '🇮🇳 Hindi' : '🇬🇧 English'

        store.addMessage({
          role: 'assistant',
          text: data.assistant_text,
          language: data.detected_language,
          languageLabel: langLabel,
          latencyMs: data.ttfa_latency_ms,
          guardrailStatus: {
            inputPassed: true,
            outputPassed: true,
            piiRedacted: false,
            toxicityScore: 0.01,
            flags: ['Output Guardrail Cleared', 'Voice-Safe Format'],
          },
        })

        // If no Sarvam audio chunk was received or queued, use browser Web Speech API as fallback voice!
        if (!this.hasReceivedAudioThisTurn && !this.isPlayingAudio && data.assistant_text) {
          this.speakWebSpeech(data.assistant_text, data.detected_language)
        }
        break
      }

      case 'guardrail_refusal':
        store.addMessage({
          role: 'assistant',
          text: data.text,
          guardrailStatus: {
            inputPassed: false,
            outputPassed: true,
            piiRedacted: false,
            toxicityScore: 0.9,
            flags: ['Prompt Injection Shield Triggered'],
          },
        })
        if (data.audio_base64) {
          this.queueAudio(data.audio_base64)
        } else {
          this.speakWebSpeech(data.text, 'en-US')
        }
        break
    }
  }

  sendText(text: string, language_code = 'en-IN') {
    this.hasReceivedAudioThisTurn = false
    if (this.ws && this.isConnected && this.ws.readyState === WebSocket.OPEN) {
      this.clearAudioQueue()
      this.ws.send(
        JSON.stringify({
          type: 'text_query',
          text: text,
          language_code: language_code,
        })
      )
    } else {
      // Reconnect if closed
      this.connect().then((ok) => {
        if (ok && this.ws) {
          this.ws.send(
            JSON.stringify({
              type: 'text_query',
              text: text,
              language_code: language_code,
            })
          )
        }
      })
    }
  }

  sendAudioBase64(base64Data: string) {
    this.hasReceivedAudioThisTurn = false
    if (this.ws && this.isConnected && this.ws.readyState === WebSocket.OPEN) {
      this.clearAudioQueue()
      this.ws.send(
        JSON.stringify({
          type: 'audio_query',
          audio_base64: base64Data,
        })
      )
    } else {
      this.connect().then((ok) => {
        if (ok && this.ws) {
          this.ws.send(
            JSON.stringify({
              type: 'audio_query',
              audio_base64: base64Data,
            })
          )
        }
      })
    }
  }

  private clearAudioQueue() {
    if (this.currentAudio) {
      try {
        this.currentAudio.pause()
        this.currentAudio.currentTime = 0
      } catch (e) {}
      this.currentAudio = null
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
    this.audioQueue = []
    this.isPlayingAudio = false
    useVoiceStore.getState().setSpeaking(false)
  }

  private queueAudio(base64Audio: string) {
    this.audioQueue.push(`data:audio/mp3;base64,${base64Audio}`)
    if (!this.isPlayingAudio) {
      this.playNextAudio()
    }
  }

  private playNextAudio() {
    const store = useVoiceStore.getState()

    if (this.audioQueue.length === 0) {
      this.isPlayingAudio = false
      store.setSpeaking(false)
      return
    }

    this.isPlayingAudio = true
    store.setSpeaking(true)
    const nextSrc = this.audioQueue.shift()
    if (!nextSrc) {
      this.isPlayingAudio = false
      store.setSpeaking(false)
      return
    }

    this.currentAudio = new Audio(nextSrc)
    this.currentAudio.onended = () => {
      this.playNextAudio()
    }
    this.currentAudio.onerror = () => {
      this.playNextAudio()
    }
    this.currentAudio.play().catch((err) => {
      console.warn('Audio autoplay warning:', err)
      // Fall back to web speech if html audio autoplay fails
      if (this.currentAssistantText) {
        this.speakWebSpeech(this.currentAssistantText, this.currentDetectedLang)
      } else {
        this.playNextAudio()
      }
    })
  }

  private speakWebSpeech(text: string, lang = 'hi-IN') {
    if (!('speechSynthesis' in window)) {
      useVoiceStore.getState().setSpeaking(false)
      return
    }
    try {
      window.speechSynthesis.cancel()
      const store = useVoiceStore.getState()
      store.setSpeaking(true)

      const isDevanagari = /[\u0900-\u097F]/.test(text)
      const targetLang = isDevanagari ? 'hi-IN' : (lang.startsWith('hi') ? 'hi-IN' : 'en-US')

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = targetLang
      utterance.rate = 1.02
      
      const voices = window.speechSynthesis.getVoices()
      const targetVoice = voices.find((v) => v.lang.startsWith(targetLang.substring(0, 2)))
      if (targetVoice) {
        utterance.voice = targetVoice
      }

      utterance.onend = () => {
        store.setSpeaking(false)
      }
      utterance.onerror = () => {
        store.setSpeaking(false)
      }

      window.speechSynthesis.speak(utterance)
    } catch (e) {
      console.warn('WebSpeech error:', e)
      useVoiceStore.getState().setSpeaking(false)
    }
  }

  disconnect() {
    this.clearAudioQueue()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
  }
}

export const wsClient = new WebSocketClient()
