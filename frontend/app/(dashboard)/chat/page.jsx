'use client'
import { useState, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { Brain, AlertCircle, ChevronRight } from 'lucide-react'
import ChatInterface from '@/components/chat/ChatInterface'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { apiClient } from '@/lib/api/client'

export default function ChatPage() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const sessionId = searchParams.get('session_id')
    const [sessionData, setSessionData] = useState(null)
    const [history, setHistory] = useState([])

    useEffect(() => {
        if (sessionId) {
            apiClient.get(`/api/v1/analyze/result/${sessionId}`) // assuming a generalized endpoint or history
                .then(res => setSessionData(res.data))
                .catch(err => console.error(err))
        }
        apiClient.get('/api/v1/users/sessions?limit=3')
            .then(res => setHistory(res.data.sessions))
            .catch(err => console.error(err))
    }, [sessionId])

    if (!sessionId) {
        return (
            <ProtectedRoute>
                <div className="flex flex-col items-center justify-center h-[80vh] px-4">
                    <div className="bg-navy-800 p-8 rounded-2xl border border-navy-700 text-center max-w-md shadow-xl">
                        <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
                        <h2 className="text-xl font-bold text-white mb-2">No Session Selected</h2>
                        <p className="text-gray-400 mb-6">Please upload a scan or select a past analysis to chat with the AI assistant.</p>
                        <button onClick={() => router.push('/upload')} className="px-6 py-2 bg-teal-600 text-white rounded hover:bg-teal-500 transition">
                            Go to Upload
                        </button>
                    </div>
                </div>
            </ProtectedRoute>
        )
    }

    return (
        <ProtectedRoute>
            <div className="max-w-7xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-4 gap-6">
                {/* LEFT SIDEBAR */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-navy-800 p-5 rounded-xl border border-navy-700">
                        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Current Session</h3>
                        {sessionData ? (
                            <div>
                                <div className="flex items-center gap-2 mb-3">
                                    <span className={`px-2 py-1 text-xs font-bold rounded-md ${sessionData.vision?.risk_level === 'HIGH' ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-teal-500/20 text-teal-400 border border-teal-500/30'}`}>
                                        {sessionData.vision?.risk_level || 'UNKNOWN'} RISK
                                    </span>
                                    <span className="text-sm text-gray-300">{sessionData.patient_id || 'Anonymous'}</span>
                                </div>
                                <p className="text-lg font-bold text-white mb-1">{sessionData.nlp?.primary_diagnosis || 'Pending'}</p>
                                <button onClick={() => router.push(`/results?session_id=${sessionId}`)} className="text-sm text-teal-400 hover:text-teal-300 flex items-center mt-4">
                                    View Full Results <ChevronRight className="w-4 h-4 ml-1" />
                                </button>
                            </div>
                        ) : (
                            <div className="animate-pulse flex flex-col gap-2">
                                <div className="h-4 bg-navy-700 rounded w-1/2"></div>
                                <div className="h-6 bg-navy-700 rounded w-3/4"></div>
                            </div>
                        )}
                    </div>

                    {history.length > 0 && (
                        <div className="bg-navy-800 p-5 rounded-xl border border-navy-700">
                            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Recent Sessions</h3>
                            <div className="space-y-3">
                                {history.map(item => (
                                    <div key={item.id} onClick={() => router.push(`/chat?session_id=${item.id}`)} className="cursor-pointer p-3 rounded-lg border border-navy-700 bg-navy-900/50 hover:border-teal-500/30 transition">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-xs text-gray-400">{new Date(item.created_at).toLocaleDateString()}</span>
                                        </div>
                                        <p className="text-sm text-gray-200 truncate">{item.patient_id || 'Anonymous'}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* MAIN CHAT AREA */}
                <div className="lg:col-span-3 flex flex-col bg-navy-800 border border-navy-700 rounded-xl overflow-hidden h-[80vh]">
                    <div className="p-4 bg-navy-900 border-b border-navy-700 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Brain className="w-6 h-6 text-teal-500" />
                            <h2 className="font-semibold text-white">Medical AI Assistant</h2>
                        </div>
                        <span className="text-xs text-yellow-500 bg-yellow-500/10 px-3 py-1 rounded-full border border-yellow-500/20">
                            Not a substitute for medical advice
                        </span>
                    </div>
                    {/* Re-use the ChatInterface component created in Prompt 36 */}
                    <div className="flex-1 overflow-hidden">
                        <ChatInterface sessionId={sessionId} />
                    </div>
                </div>
            </div>
        </ProtectedRoute>
    )
}
