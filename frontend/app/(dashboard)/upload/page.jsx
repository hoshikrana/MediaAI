'use client'
import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Upload, X, Loader2 } from 'lucide-react'
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

    // Cleanup object URL
    useEffect(() => {
        return () => {
            if (previewUrl) URL.revokeObjectURL(previewUrl)
        }
    }, [previewUrl])

    const handleFile = (selectedFile) => {
        setError(null)
        if (!selectedFile) return
        
        const validTypes = ['image/jpeg', 'image/png']
        if (!validTypes.includes(selectedFile.type)) {
            setError("Invalid file type (PNG or JPG only)")
            return
        }
        if (selectedFile.size > 10 * 1024 * 1024) {
            setError("File too large (max 10MB)")
            return
        }
        
        setFile(selectedFile)
        setPreviewUrl(URL.createObjectURL(selectedFile))
    }

    const onDrop = (e) => {
        e.preventDefault()
        setDragActive(false)
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0])
        }
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
            // Redirect to results page immediately; polling happens there
            router.push(`/results?session_id=${res.data.session_id}&task_id=${res.data.task_id}`)
        } catch (err) {
            setError(err.response?.data?.message || "Failed to submit analysis. Please try again.")
            setIsSubmitting(false)
        }
    }

    const quickChips = ["Chest pain", "Shortness of breath", "Fever", "Cough", "Fatigue", "Dyspnea"]

    return (
        <ProtectedRoute>
            <div className="max-w-6xl mx-auto px-4 py-8">
                <h1 className="text-3xl font-bold text-white mb-8">New Analysis Session</h1>
                
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                    {/* LEFT COLUMN (60%) */}
                    <div className="lg:col-span-3 space-y-6">
                        
                        {/* Dropzone */}
                        <div 
                            className={`relative flex flex-col items-center justify-center w-full h-64 lg:h-80 border-2 border-dashed rounded-xl transition-colors ${
                                dragActive ? 'border-teal-500 bg-teal-500/5' : 'border-navy-600 bg-navy-800/50 hover:bg-navy-800'
                            }`}
                            onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
                            onDragLeave={() => setDragActive(false)}
                            onDrop={onDrop}
                        >
                            {!previewUrl ? (
                                <div className="text-center px-4">
                                    <Upload className="w-12 h-12 text-teal-500 mx-auto mb-4" />
                                    <p className="text-lg text-gray-300 font-medium">Drop chest X-ray here</p>
                                    <p className="text-sm text-gray-500 mt-2">or</p>
                                    <button onClick={() => fileInputRef.current?.click()} className="mt-2 text-teal-400 hover:text-teal-300 font-medium">
                                        click to browse
                                    </button>
                                </div>
                            ) : (
                                <div className="relative w-full h-full flex items-center justify-center bg-gray-900 rounded-xl overflow-hidden group">
                                    <img src={previewUrl} alt="Preview" className="max-w-full max-h-full object-contain" data-testid="image-preview" />
                                    <button 
                                        onClick={() => { setFile(null); setPreviewUrl(null) }}
                                        className="absolute top-4 right-4 bg-red-500 text-white p-1.5 rounded-full hover:bg-red-600 shadow opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>
                            )}
                            <input 
                                type="file" ref={fileInputRef} className="hidden" accept="image/jpeg, image/png"
                                onChange={(e) => handleFile(e.target.files[0])}
                            />
                        </div>
                        {error && <p className="text-red-400 text-sm font-medium" data-testid="file-error">{error}</p>}

                        {/* Symptoms */}
                        <div className="bg-navy-800 p-6 rounded-xl border border-navy-700">
                            <label className="block text-sm font-medium text-gray-300 mb-2">Clinical Notes / Symptoms</label>
                            <textarea 
                                value={symptoms}
                                onChange={(e) => setSymptoms(e.target.value)}
                                placeholder="Describe patient symptoms, medical history... Example: 'Patient presents with productive cough for 3 weeks...'"
                                className="w-full min-h-[150px] p-3 bg-navy-900 border border-navy-600 rounded-lg text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent resize-y"
                                maxLength={2000}
                            />
                            <div className="flex justify-between items-center mt-2">
                                <span className="text-xs text-gray-500">{symptoms.length} / 2000</span>
                            </div>
                            
                            <div className="mt-4">
                                <p className="text-xs text-gray-400 mb-2">Quick tags:</p>
                                <div className="flex flex-wrap gap-2">
                                    {quickChips.map(chip => (
                                        <button key={chip} onClick={() => appendSymptom(chip)} className="px-3 py-1 bg-navy-700 text-teal-400 text-xs rounded-full hover:bg-navy-600 border border-navy-600 transition">
                                            + {chip}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="mt-6 border-t border-navy-700 pt-4">
                                <p className="text-sm text-gray-400 mb-3">Or use voice input:</p>
                                <VoiceInput onTranscribed={(text) => appendSymptom(text)} />
                            </div>
                        </div>
                    </div>

                    {/* RIGHT COLUMN (40%) */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="bg-navy-800 p-6 rounded-xl border border-navy-700">
                            <h3 className="text-lg font-medium text-white mb-4">Session Details</h3>
                            
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Patient ID (Optional)</label>
                                    <input 
                                        type="text" value={patientId} onChange={(e) => setPatientId(e.target.value)}
                                        placeholder="PT-2024-001"
                                        className="w-full p-2.5 bg-navy-900 border border-navy-600 rounded-lg text-white focus:ring-1 focus:ring-teal-500"
                                    />
                                    <p className="text-xs text-gray-500 mt-2 flex items-start gap-1">
                                        <span>ℹ️</span> No identifying information is stored. ID is for your reference only.
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="bg-navy-800 p-6 rounded-xl border border-navy-700">
                            <h3 className="text-lg font-medium text-white mb-4">Ready to Analyze</h3>
                            
                            <ul className="space-y-3 mb-6 text-sm">
                                <li className={`flex items-center gap-2 ${file ? 'text-green-400' : 'text-gray-500'}`}>
                                    {file ? <CheckCircle className="w-4 h-4" /> : <div className="w-4 h-4 rounded-sm border border-gray-500" />}
                                    Chest X-ray uploaded
                                </li>
                                <li className={`flex items-center gap-2 ${symptoms.trim() ? 'text-green-400' : 'text-gray-500'}`}>
                                    {symptoms.trim() ? <CheckCircle className="w-4 h-4" /> : <div className="w-4 h-4 rounded-sm border border-gray-500" />}
                                    Symptoms provided (Optional)
                                </li>
                            </ul>

                            <button 
                                onClick={handleSubmit}
                                disabled={!file || isSubmitting}
                                data-testid="analyze-button"
                                className="w-full py-3 rounded-lg font-bold text-white transition-all flex items-center justify-center gap-2 disabled:bg-navy-600 disabled:text-gray-400 disabled:cursor-not-allowed bg-teal-600 hover:bg-teal-500 shadow-lg"
                            >
                                {isSubmitting ? (
                                    <><Loader2 className="w-5 h-5 animate-spin" /> Submitting...</>
                                ) : (
                                    <><Brain className="w-5 h-5" /> Analyze Scan</>
                                )}
                            </button>
                            <p className="text-xs text-center text-gray-500 mt-3">⏱ Analysis takes approximately 30-60 seconds</p>
                        </div>
                    </div>
                </div>
            </div>
        </ProtectedRoute>
    )
}

function CheckCircle({ className }) {
    return (
        <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
    )
}
