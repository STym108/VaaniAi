export interface AudioRecorderResult {
  blob: Blob
  transcript: string
}

export class AudioRecorder {
  private mediaStream: MediaStream | null = null
  private mediaRecorder: MediaRecorder | null = null
  private audioContext: AudioContext | null = null
  private analyser: AnalyserNode | null = null
  private animationFrameId: number | null = null
  private recordedChunks: Blob[] = []
  private recognition: any = null
  private liveTranscript = ''

  private onVolumeChange?: (volume: number) => void

  constructor(onVolumeChange?: (volume: number) => void) {
    this.onVolumeChange = onVolumeChange
  }

  async start(): Promise<void> {
    this.recordedChunks = []
    this.liveTranscript = ''
    
    // 1. Request microphone access
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    })

    // 2. Setup Web Audio Analyser for live volume metering
    this.audioContext = new (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext)()
    const source = this.audioContext.createMediaStreamSource(this.mediaStream)
    this.analyser = this.audioContext.createAnalyser()
    this.analyser.fftSize = 256
    source.connect(this.analyser)

    this.startVolumeMonitoring()

    // 3. Initialize MediaRecorder
    this.mediaRecorder = new MediaRecorder(this.mediaStream, {
      mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4',
    })

    this.mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        this.recordedChunks.push(event.data)
      }
    }

    this.mediaRecorder.start(100) // 100ms slices

    // 4. Initialize Web SpeechRecognition for instant local transcription
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognition) {
      try {
        this.recognition = new SpeechRecognition()
        this.recognition.continuous = true
        this.recognition.interimResults = true
        this.recognition.lang = 'hi-IN' // Auto multi-lang / Hindi priority

        this.recognition.onresult = (event: any) => {
          let transcriptStr = ''
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            transcriptStr += event.results[i][0].transcript
          }
          if (transcriptStr.trim()) {
            this.liveTranscript = transcriptStr.trim()
          }
        }

        this.recognition.start()
      } catch (e) {
        console.warn('SpeechRecognition failed to start:', e)
      }
    }
  }

  private startVolumeMonitoring() {
    if (!this.analyser) return

    const bufferLength = this.analyser.frequencyBinCount
    const dataArray = new Uint8Array(bufferLength)

    const updateVolume = () => {
      if (!this.analyser) return

      this.analyser.getByteFrequencyData(dataArray)
      let sum = 0
      for (let i = 0; i < bufferLength; i++) {
        sum += dataArray[i]
      }
      const average = sum / bufferLength
      const normalizedVolume = Math.min(1, average / 100)

      if (this.onVolumeChange) {
        this.onVolumeChange(normalizedVolume)
      }

      this.animationFrameId = requestAnimationFrame(updateVolume)
    }

    updateVolume()
  }

  async stop(): Promise<AudioRecorderResult> {
    return new Promise((resolve) => {
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId)
        this.animationFrameId = null
      }

      if (this.onVolumeChange) {
        this.onVolumeChange(0)
      }

      if (this.recognition) {
        try {
          this.recognition.stop()
        } catch (e) {}
      }

      const capturedTranscript = this.liveTranscript

      if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
        this.mediaRecorder.onstop = () => {
          const audioBlob = new Blob(this.recordedChunks, {
            type: this.mediaRecorder?.mimeType || 'audio/webm',
          })
          this.cleanup()
          resolve({
            blob: audioBlob,
            transcript: capturedTranscript,
          })
        }
        this.mediaRecorder.stop()
      } else {
        this.cleanup()
        resolve({
          blob: new Blob([], { type: 'audio/webm' }),
          transcript: capturedTranscript,
        })
      }
    })
  }

  private cleanup() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop())
      this.mediaStream = null
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close()
      this.audioContext = null
    }
    this.mediaRecorder = null
    this.analyser = null
    this.recognition = null
  }
}
