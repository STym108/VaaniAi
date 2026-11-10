import React, { useEffect, useRef } from 'react'
import { useVoiceStore } from '../store/useVoiceStore'

export const AudioVisualizer: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const { isRecording, isSpeaking, liveVolume } = useVoiceStore()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationId: number
    let phase = 0

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      const width = canvas.width
      const height = canvas.height
      const centerY = height / 2

      const bars = 28
      const barWidth = 3
      const spacing = (width - bars * barWidth) / (bars - 1)

      const active = isRecording || isSpeaking
      const amp = isRecording ? Math.max(0.15, liveVolume * 1.6) : isSpeaking ? 0.6 : 0.05

      for (let i = 0; i < bars; i++) {
        const x = i * (barWidth + spacing)
        // Multi-frequency wave calculation
        const sinVal = Math.sin(phase + i * 0.35) * Math.cos(phase * 0.8 + i * 0.15)
        const barHeight = Math.max(3, Math.abs(sinVal) * (height * 0.85) * amp)

        const y = centerY - barHeight / 2

        // Create warm gold to terracotta gradient
        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight)
        if (isRecording) {
          gradient.addColorStop(0, '#D97D54')
          gradient.addColorStop(1, '#DFB15B')
        } else if (isSpeaking) {
          gradient.addColorStop(0, '#DFB15B')
          gradient.addColorStop(1, '#689F77')
        } else {
          gradient.addColorStop(0, 'rgba(223, 177, 91, 0.25)')
          gradient.addColorStop(1, 'rgba(200, 138, 72, 0.15)')
        }

        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.roundRect(x, y, barWidth, barHeight, 2)
        ctx.fill()
      }

      phase += active ? 0.1 : 0.02
      animationId = requestAnimationFrame(render)
    }

    render()

    return () => {
      cancelAnimationFrame(animationId)
    }
  }, [isRecording, isSpeaking, liveVolume])

  return (
    <div className="w-full flex justify-center py-2">
      <canvas
        ref={canvasRef}
        width={320}
        height={48}
        className="w-80 h-12 rounded-lg"
      />
    </div>
  )
}
