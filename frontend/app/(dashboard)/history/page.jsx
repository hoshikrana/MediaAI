'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { FolderOpen, Eye, MessageSquare, Trash2, Filter } from 'lucide-react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { apiClient } from '@/lib/api/client'

export default function HistoryPage() {
    const router = useRouter()
    const [sessions, setSessions] = useState([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [isLoading, setIsLoading] = useState(true)

    const fetchHistory = async () => {
        try {
            setIsLoading(true)
            const res = await apiClient.get(`/api/v1/users/sessions?page=${page}&limit=10`)
            setSessions(res.data.sessions)
            setTotal(res.data.total)
        } catch (e) {
            console.error(e)
        } finally {
            setIsLoading(false)
        }
    }

    useEffect(() => {
        fetchHistory()
    }, [page])

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this session?")) return
        try {
            await apiClient.delete(`/api/v1/analyze/${id}`) // assuming task_id/session_id alignment
            fetchHistory()
        } catch (e) {
            alert("Failed to delete")
        }
    }

    return (
        <ProtectedRoute>
            <div className="max-w-6xl mx-auto px-4 py-8">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-white">Analysis History</h1>
                    <button onClick={() => router.push('/upload')} className="px-4 py-2 bg-teal-600 text-white rounded hover:bg-teal-500 transition">
                        + New Analysis
                    </button>
                </div>

                <div className="bg-navy-800 border border-navy-700 rounded-xl overflow-hidden shadow-lg">
                    <div className="p-4 border-b border-navy-700 flex justify-between items-center bg-navy-900/50">
                        <span className="text-sm text-gray-400">Showing {Math.min((page - 1) * 10 + 1, total)}-{Math.min(page * 10, total)} of {total} analyses</span>
                        <div className="flex items-center gap-2">
                            <Filter className="w-4 h-4 text-gray-400" />
                            <select className="bg-navy-900 border border-navy-600 text-sm rounded p-1 text-gray-300">
                                <option>All Risks</option>
                                <option>High Risk</option>
                                <option>Medium Risk</option>
                                <option>Low Risk</option>
                            </select>
                        </div>
                    </div>

                    {isLoading ? (
                        <div className="p-12 flex justify-center"><div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div></div>
                    ) : sessions.length === 0 ? (
                        <div className="p-16 text-center flex flex-col items-center">
                            <FolderOpen className="w-16 h-16 text-navy-600 mb-4" />
                            <h3 className="text-xl font-medium text-white mb-2">No analyses yet</h3>
                            <button onClick={() => router.push('/upload')} className="text-teal-400 hover:text-teal-300 underline">Upload your first scan</button>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-navy-900/50 text-gray-400 border-b border-navy-700 uppercase">
                                    <tr>
                                        <th className="p-4 font-medium">Date</th>
                                        <th className="p-4 font-medium">Patient ID</th>
                                        <th className="p-4 font-medium">Risk Level</th>
                                        <th className="p-4 font-medium">Status</th>
                                        <th className="p-4 font-medium text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-navy-700">
                                    {sessions.map(s => (
                                        <tr key={s.id} className="hover:bg-navy-700/30 transition">
                                            <td className="p-4 text-gray-300">{new Date(s.created_at).toLocaleDateString()} {new Date(s.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</td>
                                            <td className="p-4 text-white font-medium">{s.patient_id || "Anonymous"}</td>
                                            <td className="p-4">
                                                <span className={`px-2 py-1 text-xs font-bold rounded-md ${s.risk_level === 'HIGH' ? 'bg-red-500/20 text-red-400' : s.risk_level === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-teal-500/20 text-teal-400'}`}>
                                                    {s.risk_level || "UNKNOWN"}
                                                </span>
                                            </td>
                                            <td className="p-4 text-gray-300">{s.status}</td>
                                            <td className="p-4 flex justify-end gap-3">
                                                <button onClick={() => router.push(`/results?session_id=${s.id}`)} className="text-gray-400 hover:text-teal-400" title="View Results"><Eye className="w-5 h-5" /></button>
                                                <button onClick={() => router.push(`/chat?session_id=${s.id}`)} className="text-gray-400 hover:text-teal-400" title="Open Chat"><MessageSquare className="w-5 h-5" /></button>
                                                <button onClick={() => handleDelete(s.id)} className="text-gray-400 hover:text-red-400" title="Delete"><Trash2 className="w-5 h-5" /></button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                    
                    {/* Pagination */}
                    <div className="p-4 border-t border-navy-700 flex justify-between items-center bg-navy-900/50">
                        <button disabled={page === 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 bg-navy-800 text-white rounded hover:bg-navy-700 disabled:opacity-50">Previous</button>
                        <span className="text-sm text-gray-400">Page {page}</span>
                        <button disabled={page * 10 >= total} onClick={() => setPage(p => p + 1)} className="px-3 py-1 bg-navy-800 text-white rounded hover:bg-navy-700 disabled:opacity-50">Next</button>
                    </div>
                </div>
            </div>
        </ProtectedRoute>
    )
}
