'use client'
import { useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Download, MessageSquare, UploadCloud, AlertTriangle, AlertCircle, Loader2 } from 'lucide-react'
import { useAnalysisStatus } from '@/lib/hooks/useAnalysisStatus'
import ProtectedRoute from '@/components/auth/ProtectedRoute'

export default function ResultsDashboard() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const taskId = searchParams.get('task_id')
    const sessionId = searchParams.get('session_id')
    
    const { status, result, error, queuePosition, estimatedWait } = useAnalysisStatus(taskId)
    const [viewMode, setViewMode] = useState('overlay') // original, heatmap, overlay

    if (error) {
        return (
            <div className="flex flex-col items-center justify-center h-[80vh] text-center px-4">
                <AlertTriangle className="w-16 h-16 text-red-500 mb-4" />
                <h2 className="text-2xl font-bold text-white mb-2">Analysis Failed</h2>
                <p className="text-red-400 mb-6">{error}</p>
                <button onClick={() => router.push('/upload')} className="px-6 py-2 bg-navy-700 text-white rounded hover:bg-navy-600 transition">Try Again</button>
            </div>
        )
    }

    if (status !== "COMPLETED" || !result) {
        return (
            <div className="flex flex-col items-center justify-center h-[80vh] px-4" data-testid="progress-tracker">
                <div className="w-full max-w-md bg-navy-800 p-8 rounded-2xl border border-navy-700 text-center shadow-xl">
                    <Loader2 className="w-12 h-12 text-teal-500 animate-spin mx-auto mb-6" />
                    <h2 className="text-2xl font-bold text-white mb-2">
                        {status === "PENDING" ? "In Queue..." : "Analyzing Data..."}
                    </h2>
                    {status === "PENDING" && queuePosition && (
                        <p className="text-gray-400 mb-2">Position in queue: {queuePosition}</p>
                    )}
                    <p className="text-gray-500 text-sm">
                        Estimated wait: {estimatedWait ? `${estimatedWait}s` : "Calculating..."}
                    </p>
                    
                    <div className="mt-8 space-y-3 text-left">
                        {/* Fake progress steps for UX */}
                        {['Queue position secured', 'Vision models loading', 'Extracting features', 'Running MedCLIP Fusion'].map((step, i) => (
                            <div key={i} className={`flex items-center gap-3 text-sm ${status === "PROCESSING" && i < 2 ? 'text-teal-400' : 'text-gray-500'}`}>
                                <div className={`w-2 h-2 rounded-full ${status === "PROCESSING" && i < 2 ? 'bg-teal-500' : 'bg-gray-600'}`} />
                                {step}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        )
    }

    const { vision, nlp, fusion, report_text, warnings, timings } = result

    // Derived styles
    const isHighRisk = vision?.risk_level === "HIGH" || fusion?.final_risk === "HIGH"
    const isMediumRisk = vision?.risk_level === "MEDIUM" || fusion?.final_risk === "MEDIUM"
    
    const bannerClass = isHighRisk 
        ? "bg-gradient-to-r from-red-900/80 to-red-800/80 border-red-500/50" 
        : isMediumRisk 
        ? "bg-gradient-to-r from-amber-900/80 to-amber-800/80 border-amber-500/50"
        : "bg-gradient-to-r from-teal-900/80 to-teal-800/80 border-teal-500/50"

    const highlightText = (text, rawEntities) => {
        if (!text || !rawEntities) return { __html: text }
        // For simplicity, returning plain text if custom dangerouslySetInnerHTML function highlight_entities isn't imported
        // Assume highlight_entities is imported from a utils file in a real build
        return { __html: text } 
    }

    return (
        <ProtectedRoute>
            <div className="max-w-7xl mx-auto px-4 py-8 space-y-6">
                
                {warnings?.length > 0 && (
                    <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-yellow-900/30 border border-yellow-500/30 rounded-lg flex gap-3 text-yellow-200 text-sm">
                        <AlertCircle className="w-5 h-5 shrink-0" />
                        <div>
                            <p className="font-bold mb-1">Partial Analysis Warning</p>
                            <ul className="list-disc pl-4">
                                {warnings.map((w, i) => <li key={i}>{w}</li>)}
                            </ul>
                        </div>
                    </motion.div>
                )}

                {/* PANEL 1: RISK BANNER */}
                <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} className={`p-6 rounded-2xl border flex flex-col md:flex-row items-center justify-between shadow-2xl relative overflow-hidden ${bannerClass}`} data-testid="risk-banner">
                    {isHighRisk && <div className="absolute inset-0 border-4 border-red-500/30 rounded-2xl animate-pulse-ring" />}
                    <div className="relative z-10 text-center md:text-left mb-4 md:mb-0">
                        <h2 className="text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
                            {isHighRisk ? '🔴 HIGH RISK DETECTED' : isMediumRisk ? '🟡 MEDIUM RISK' : '🟢 LOW RISK'}
                        </h2>
                        <p className="text-white/70 mt-1">Processed in {(timings.total_ms / 1000).toFixed(1)} seconds</p>
                    </div>
                    <div className="relative z-10 text-center md:text-right">
                        <div className="text-5xl font-black text-white font-mono">
                            {vision?.anomaly_score?.toFixed(1) || '--'}<span className="text-2xl text-white/50">/100</span>
                        </div>
                        <p className="text-white/70 font-medium tracking-wide uppercase text-sm mt-1">Anomaly Score</p>
                    </div>
                </motion.div>

                {/* PANEL 2: TWO-COLUMN GRID */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    
                    {/* Left: Heatmap */}
                    <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }} className="bg-navy-800 border border-navy-700 rounded-2xl p-6 flex flex-col" data-testid="heatmap-viewer">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-semibold text-lg">Imaging Findings</h3>
                            <div className="flex bg-navy-900 rounded-lg p-1 border border-navy-700">
                                {['original', 'heatmap', 'overlay'].map(mode => (
                                    <button 
                                        key={mode} onClick={() => setViewMode(mode)}
                                        className={`px-3 py-1 text-xs font-medium rounded-md capitalize transition ${viewMode === mode ? 'bg-navy-700 text-white shadow' : 'text-gray-400 hover:text-white'}`}
                                    >
                                        {mode}
                                    </button>
                                ))}
                            </div>
                        </div>
                        
                        <div className="relative flex-1 bg-black rounded-xl overflow-hidden min-h-[300px] flex items-center justify-center border border-navy-600">
                            {vision?.heatmap_base64 ? (
                                <img 
                                    src={vision.heatmap_base64} 
                                    alt="Analysis Result" 
                                    className="max-w-full max-h-full object-contain"
                                    style={{
                                        // The base64 from backend contains a 3-panel image (Original|Heatmap|Overlay).
                                        // A real frontend would slice it using CSS object-position, or the backend would return them separately.
                                        // For this demo, we assume the backend handles the view state or we just show the full panel.
                                    }}
                                />
                            ) : (
                                <p className="text-gray-500">Image analysis unavailable</p>
                            )}
                        </div>
                    </motion.div>

                    {/* Right: Diagnosis */}
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.2 }} className="bg-navy-800 border border-navy-700 rounded-2xl p-6 flex flex-col">
                        <h3 className="font-semibold text-lg mb-6">Clinical Assessment</h3>
                        
                        {nlp ? (
                            <div className="space-y-6">
                                <div>
                                    <p className="text-sm text-gray-400 mb-1">Primary Impression</p>
                                    <div className="flex justify-between items-end mb-2">
                                        <p className="text-2xl font-bold text-white">{nlp.primary_diagnosis}</p>
                                        <p className="text-teal-400 font-mono">{(nlp.diagnosis_confidence * 100).toFixed(0)}%</p>
                                    </div>
                                    <div className="w-full bg-navy-900 rounded-full h-2.5 overflow-hidden">
                                        <motion.div initial={{ width: 0 }} animate={{ width: `${nlp.diagnosis_confidence * 100}%` }} className="bg-teal-500 h-2.5 rounded-full" />
                                    </div>
                                </div>

                                {nlp.differential?.length > 0 && (
                                    <div className="bg-navy-900/50 p-4 rounded-xl border border-navy-700">
                                        <p className="text-sm text-gray-400 mb-3">Differential Diagnosis</p>
                                        <div className="space-y-3">
                                            {nlp.differential.map((diff, idx) => (
                                                <div key={idx}>
                                                    <div className="flex justify-between text-sm mb-1 text-gray-300">
                                                        <span>{diff.disease}</span>
                                                        <span className="font-mono">{(diff.confidence * 100).toFixed(0)}%</span>
                                                    </div>
                                                    <div className="w-full bg-navy-800 rounded-full h-1.5 overflow-hidden">
                                                        <motion.div initial={{ width: 0 }} animate={{ width: `${diff.confidence * 100}%` }} transition={{ delay: 0.5 }} className="bg-gray-500 h-1.5 rounded-full" />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {fusion && (
                                    <div className={`p-4 rounded-xl border ${fusion.alignment === 'HIGH' ? 'bg-green-900/20 border-green-500/30' : 'bg-yellow-900/20 border-yellow-500/30'}`}>
                                        <p className="text-sm font-semibold mb-1 flex items-center gap-2">
                                            {fusion.alignment === 'HIGH' ? '✅ High Image-Text Alignment' : '⚠️ Moderate Alignment'}
                                        </p>
                                        <p className="text-xs text-gray-400">
                                            Image features and clinical notes match with {(fusion.image_text_similarity * 100).toFixed(0)}% similarity.
                                        </p>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="flex-1 flex items-center justify-center">
                                <p className="text-gray-500">NLP analysis skipped or unavailable.</p>
                            </div>
                        )}
                    </motion.div>
                </div>

                {/* PANEL 4: AI REPORT */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-navy-800 border border-navy-700 rounded-2xl p-6" data-testid="ai-report">
                    <h3 className="font-semibold text-lg mb-4 text-teal-400">AI Narrative Report</h3>
                    <div className="prose prose-invert max-w-none mb-8 text-gray-300">
                        {/* Rendering plain text with line breaks for now */}
                        {report_text?.split('\n').map((line, i) => (
                            <p key={i} className="mb-2 leading-relaxed">{line}</p>
                        ))}
                    </div>

                    <div className="flex flex-wrap gap-4 pt-6 border-t border-navy-700">
                        <button className="flex items-center gap-2 px-6 py-2.5 bg-navy-700 text-white rounded-lg hover:bg-navy-600 border border-navy-600 transition">
                            <Download className="w-4 h-4" /> Download PDF
                        </button>
                        <button onClick={() => router.push(`/chat?session_id=${sessionId}`)} className="flex items-center gap-2 px-6 py-2.5 bg-teal-600 text-white rounded-lg hover:bg-teal-500 shadow transition">
                            <MessageSquare className="w-4 h-4" /> Discuss Findings with AI
                        </button>
                        <button onClick={() => router.push('/upload')} className="flex items-center gap-2 px-6 py-2.5 bg-transparent text-gray-400 rounded-lg hover:text-white transition ml-auto">
                            <UploadCloud className="w-4 h-4" /> New Scan
                        </button>
                    </div>
                </motion.div>
            </div>
        </ProtectedRoute>
    )
}
