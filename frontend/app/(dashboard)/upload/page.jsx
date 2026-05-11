'use client'
import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Upload, X, Loader2, Brain, Mic, FileImage, AlertCircle, CheckCircle2, Sparkles } from 'lucide-react'
import { apiClient } from '@/lib/api/client'
import VoiceInput from '@/components/analysis/VoiceInput'
import ProtectedRoute from '@/components/auth/ProtectedRoute'

export default function UploadPage() {
    const router = useRouter()
    const [file, setFile] = useState(null)
    const [previewUrl, setPreviewUrl] = useState(null)
    const [symptoms, setSymptoms] = useState("")
    const [patientId, setPatientId] = useState("")
    const [error, setError] = useState(null)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [dragActive, setDragActive] = useState(false)
    const fileInputRef = useRef(null)

    useEffect(() => {
        return () => { if (previewUrl) URL.revokeObjectURL(previewUrl) }
    }, [previewUrl])

    const handleFile = (selectedFile) => {
        setError(null)
        if (!selectedFile) return
        const validTypes = ['image/jpeg', 'image/png']
        if (!validTypes.includes(selectedFile.type)) {
            setError("Invalid file type. Please upload a PNG or JPG image.")
            return
        }
        if (selectedFile.size > 10 * 1024 * 1024) {
            setError("File too large. Maximum size is 10MB.")
            return
        }
        setFile(selectedFile)
        setPreviewUrl(URL.createObjectURL(selectedFile))
    }

    const onDrop = (e) => {
        e.preventDefault()
        setDragActive(false)
        if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0])
    }

    const appendSymptom = (text) => {
        setSymptoms(prev => prev ? `${prev}, ${text}` : text)
    }

    const handleSubmit = async () => {
        if (!file) return
        setIsSubmitting(true)
        setError(null)
        const formData = new FormData()
        formData.append("image", file)
        formData.append("symptoms_text", symptoms)
        if (patientId) formData.append("patient_id", patientId)

        try {
            const res = await apiClient.post('/api/v1/analyze', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            router.push(`/results?session_id=${res.data.session_id}&task_id=${res.data.task_id}`)
        } catch (err) {
            setError(err.response?.data?.message || "Failed to submit analysis. Please try again.")
            setIsSubmitting(false)
        }
    }

    const quickChips = ["Chest pain", "Shortness of breath", "Fever", "Cough", "Fatigue", "Dyspnea", "Wheezing", "Night sweats"]

    const checks = [
        { done: !!file, label: "Chest X-ray uploaded" },
        { done: symptoms.trim().length > 0, label: "Clinical notes provided" },
    ]

    return (
        <ProtectedRoute>
            <div className="max-w-7xl mx-auto px-4 py-10">
                {/* Header */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-10">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-10 h-10 rounded-xl bg-teal-500/10 flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-teal-400" />
                        </div>
                        <h1 className="text-3xl font-bold text-white tracking-tight">New Analysis</h1>
                    </div>
                    <p className="text-gray-400 ml-[52px]">Upload a chest X-ray and describe symptoms to begin AI-powered diagnostic analysis.</p>
                </motion.div>

                <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                    {/* LEFT COLUMN */}
                    <div className="lg:col-span-3 space-y-6">
                        {/* Dropzone */}
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                            <div
                                className={`relative flex flex-col items-center justify-center w-full min-h-[320px] rounded-2xl transition-all duration-300 cursor-pointer ${
                                    dragActive
                                        ? 'border-2 border-teal-400 bg-teal-500/5 shadow-[0_0_40px_rgba(0,212,180,0.1)]'
                                        : previewUrl
                                            ? 'border border-navy-600/50 bg-navy-800/40'
                                            : 'border-2 border-dashed border-navy-600/60 bg-navy-800/30 hover:bg-navy-800/50 hover:border-navy-500/60'
                                }`}
                                onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
                                onDragLeave={() => setDragActive(false)}
                                onDrop={onDrop}
                                onClick={() => !previewUrl && fileInputRef.current?.click()}
                            >
                                {!previewUrl ? (
                                    <div className="text-center px-4 py-8">
                                        <div className="w-16 h-16 rounded-2xl bg-navy-700/50 flex items-center justify-center mx-auto mb-5">
                                            <FileImage className="w-8 h-8 text-teal-400" />
                                        </div>
                                        <p className="text-lg text-gray-200 font-semibold mb-1">Drop chest X-ray here</p>
                                        <p className="text-sm text-gray-500 mb-4">or click to browse • PNG, JPG up to 10MB</p>
                                        <span className="inline-flex items-center gap-1.5 px-4 py-2 bg-navy-700/50 rounded-lg text-sm text-teal-400 border border-navy-600/50">
                                            <Upload className="w-4 h-4" /> Select File
                                        </span>
                                    </div>
                                ) : (
                                    <div className="relative w-full h-full min-h-[320px] flex items-center justify-center bg-black/30 rounded-2xl overflow-hidden group">
                                        <img src={previewUrl} alt="Preview" className="max-w-full max-h-[400px] object-contain" data-testid="image-preview" />
                                        <div className="absolute inset-0 bg-gradient-to-t from-navy-900/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setFile(null); setPreviewUrl(null) }}
                                            className="absolute top-4 right-4 bg-red-500/90 text-white p-2 rounded-xl hover:bg-red-500 shadow-lg opacity-0 group-hover:opacity-100 transition-all"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                        <p className="absolute bottom-4 left-4 text-sm text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity">
                                            {file?.name} ({(file?.size / 1024 / 1024).toFixed(1)}MB)
                                        </p>
                                    </div>
                                )}
                                <input type="file" ref={fileInputRef} className="hidden" accept="image/jpeg,image/png" onChange={(e) => handleFile(e.target.files[0])} />
                            </div>
                        </motion.div>

                        {error && (
                            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="flex items-center gap-2 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl" data-testid="file-error">
                                <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                                <p className="text-red-400 text-sm">{error}</p>
                            </motion.div>
                        )}

                        {/* Symptoms */}
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
                            <label className="block text-sm font-semibold text-gray-200 mb-3">Clinical Notes / Symptoms</label>
                            <textarea
                                value={symptoms}
                                onChange={(e) => setSymptoms(e.target.value)}
                                placeholder="Describe patient symptoms, medical history... Example: 'Patient presents with productive cough for 3 weeks, low-grade fever, weight loss...'"
                                className="input-field min-h-[140px] resize-y"
                                maxLength={2000}
                            />
                            <div className="flex justify-between items-center mt-2">
                                <span className="text-xs text-gray-600">{symptoms.length} / 2,000</span>
                            </div>

                            <div className="mt-5">
                                <p className="text-xs font-medium text-gray-500 mb-2.5 uppercase tracking-wider">Quick Tags</p>
                                <div className="flex flex-wrap gap-2">
                                    {quickChips.map(chip => (
                                        <button key={chip} onClick={() => appendSymptom(chip)} className="px-3 py-1.5 bg-navy-700/50 text-teal-400 text-xs rounded-lg hover:bg-navy-600/50 border border-navy-600/40 transition-all hover:border-teal-500/30 hover:shadow-sm">
                                            + {chip}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="mt-6 border-t border-navy-700/50 pt-5">
                                <p className="text-sm font-medium text-gray-300 mb-3 flex items-center gap-2">
                                    <Mic className="w-4 h-4 text-teal-400" /> Voice Input
                                </p>
                                <VoiceInput onTranscribed={(text) => appendSymptom(text)} />
                            </div>
                        </motion.div>
                    </div>

                    {/* RIGHT COLUMN */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="lg:col-span-2 space-y-6">
                        {/* Patient ID */}
                        <div className="glass-card p-6">
                            <h3 className="text-base font-semibold text-white mb-4">Session Details</h3>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">Patient ID <span className="text-gray-600">(Optional)</span></label>
                                <input
                                    type="text" value={patientId} onChange={(e) => setPatientId(e.target.value)}
                                    placeholder="PT-2024-001"
                                    className="input-field"
                                />
                                <p className="text-xs text-gray-600 mt-2 flex items-start gap-1.5">
                                    <span className="mt-0.5">🔒</span> No identifying information is stored on our servers. ID is for your reference only.
                                </p>
                            </div>
                        </div>

                        {/* Checklist + Submit */}
                        <div className="glass-card p-6">
                            <h3 className="text-base font-semibold text-white mb-5">Readiness Check</h3>

                            <ul className="space-y-3 mb-6">
                                {checks.map((check, i) => (
                                    <li key={i} className={`flex items-center gap-3 text-sm transition-colors ${check.done ? 'text-emerald-400' : 'text-gray-500'}`}>
                                        {check.done ? (
                                            <CheckCircle2 className="w-5 h-5 shrink-0" />
                                        ) : (
                                            <div className="w-5 h-5 rounded-md border-2 border-gray-600 shrink-0" />
                                        )}
                                        {check.label}
                                        {i === 1 && <span className="text-xs text-gray-600 ml-auto">Optional</span>}
                                    </li>
                                ))}
                            </ul>

                            <button
                                onClick={handleSubmit}
                                disabled={!file || isSubmitting}
                                data-testid="analyze-button"
                                className="w-full py-3.5 rounded-xl font-bold text-base transition-all flex items-center justify-center gap-2.5 disabled:bg-navy-700/50 disabled:text-gray-500 disabled:cursor-not-allowed disabled:shadow-none btn-primary"
                            >
                                {isSubmitting ? (
                                    <><Loader2 className="w-5 h-5 animate-spin" /> Processing...</>
                                ) : (
                                    <><Brain className="w-5 h-5" /> Analyze Scan</>
                                )}
                            </button>
                            <p className="text-xs text-center text-gray-600 mt-3">Analysis takes approximately 30–60 seconds</p>
                        </div>

                        {/* Info Card */}
                        <div className="glass-card p-5 border-teal-500/10">
                            <p className="text-xs text-gray-400 leading-relaxed">
                                <span className="text-teal-400 font-semibold">⚕️ Disclaimer:</span> MedSight AI is a research tool. Results are not a substitute for professional medical advice. Always consult a licensed healthcare professional.
                            </p>
                        </div>
                    </motion.div>
                </div>
            </div>
        </ProtectedRoute>
    )
}
