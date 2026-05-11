'use client'
import { useState, useRef } from 'react'
import { apiClient } from '@/lib/api/client'

export default function VoiceInput({ onTranscribed }) {
    const [isRecording, setIsRecording] = useState(false)
    const [recordingDuration, setRecordingDuration] = useState(0)
    const [isTranscribing, setIsTranscribing] = useState(false)
    const [transcribedText, setTranscribedText] = useState("")
    const [confidence, setConfidence] = useState(null)
    const [error, setError] = useState(null)
    
    const mediaRecorderRef = useRef(null)
    const chunksRef = useRef([])
    const timerRef = useRef(null)

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
            const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" })
            mediaRecorderRef.current = mediaRecorder
            chunksRef.current = []

            mediaRecorder.ondataavailable = e => chunksRef.current.push(e.data)
            mediaRecorder.onstop = () => {
                const blob = new Blob(chunksRef.current, { type: "audio/webm" })
                sendForTranscription(blob)
                stream.getTracks().forEach(track => track.stop())
            }

            mediaRecorder.start(1000)
            setIsRecording(true)
            setRecordingDuration(0)
            setError(null)
            
            timerRef.current = setInterval(() => {
                setRecordingDuration(prev => {
                    if (prev >= 59) {
                        stopRecording()
                        return 60
                    }
                    return prev + 1
                })
            }, 1000)
        } catch (err) {
            setError("Microphone access denied or unavailable.")
        }
    }

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop()
            setIsRecording(false)
            clearInterval(timerRef.current)
        }
    }

    const sendForTranscription = async (blob) => {
        setIsTranscribing(true)
        const formData = new FormData()
        formData.append("audio", blob, "recording.webm")
        
        try {
            const response = await apiClient.post('/api/v1/analyze/transcribe', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            setTranscribedText(response.data.text)
            setConfidence(response.data.confidence)
        } catch (err) {
            setError("Transcription failed. Please try again.")
        } finally {
            setIsTranscribing(false)
        }
    }

    const handleReset = () => {
        setTranscribedText("")
        setConfidence(null)
        setRecordingDuration(0)
    }

    return (
        <div className="p-4 border rounded-lg bg-gray-50">
            {!transcribedText && !isTranscribing && (
                <div className="flex flex-col items-center">
                    <button 
                        onClick={isRecording ? stopRecording : startRecording}
                        className={`w-16 h-16 rounded-full flex items-center justify-center transition-all ${
                            isRecording ? "bg-red-500 animate-pulse" : "bg-teal-500 hover:bg-teal-600"
                        }`}
                    >
                        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
                        </svg>
                    </button>
                    
                    <p className={`mt-2 font-mono ${recordingDuration > 50 ? 'text-red-500' : 'text-gray-600'}`}>
                        {Math.floor(recordingDuration / 60)}:{(recordingDuration % 60).toString().padStart(2, '0')} / 1:00
                    </p>
                    {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
                </div>
            )}

            {isTranscribing && (
                <div className="flex flex-col items-center py-4">
                    <div className="w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
                    <p className="mt-2 text-sm text-gray-600">Transcribing audio...</p>
                </div>
            )}

            {transcribedText && !isTranscribing && (
                <div className="space-y-4">
                    <div className="p-3 bg-white border rounded">
                        <p className="text-gray-800 animate-[typewriter_0.5s_steps(40,end)] overflow-hidden break-words">
                            &quot;{transcribedText}&quot;
                        </p>
                        <div className="flex items-center mt-2 text-xs">
                            <span className={confidence > 0.8 ? "text-green-600" : "text-yellow-600"}>
                                {confidence > 0.8 ? "✅" : "⚠️"} Confidence: {(confidence * 100).toFixed(0)}%
                            </span>
                        </div>
                    </div>
                    <div className="flex space-x-2">
                        <button onClick={() => onTranscribed(transcribedText)} className="px-4 py-2 text-white bg-teal-600 rounded hover:bg-teal-700">
                            Use This Text
                        </button>
                        <button onClick={handleReset} className="px-4 py-2 text-gray-700 bg-gray-200 rounded hover:bg-gray-300">
                            Re-record
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
