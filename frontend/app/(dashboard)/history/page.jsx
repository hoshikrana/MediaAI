'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { FolderOpen, Eye, MessageSquare, Trash2, Filter, Plus, Clock, ChevronLeft, ChevronRight } from 'lucide-react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { apiClient } from '@/lib/api/client'

export default function HistoryPage() {
    const router = useRouter()
    const [sessions, setSessions] = useState([])
    const [total, setTotal] = useState(0)
    const [page, setPage] = useState(1)
    const [isLoading, setIsLoading] = useState(true)
    const [filterRisk, setFilterRisk] = useState('all')

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

    useEffect(() => { fetchHistory() }, [page])

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to delete this session?")) return
        try {
            await apiClient.delete(`/api/v1/users/sessions/${id}`)
            fetchHistory()
        } catch (e) {
            alert("Failed to delete")
        }
    }

    const riskBadge = (level) => {
        const styles = {
            HIGH: 'badge-high',
            MEDIUM: 'badge-medium',
            LOW: 'badge-low',
        }
        return `badge ${styles[level] || 'bg-navy-700/50 text-gray-400 border border-navy-600/50'}`
    }

    const totalPages = Math.ceil(total / 10)

    return (
        <ProtectedRoute>
            <div className="max-w-7xl mx-auto px-4 py-10">
                {/* Header */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <div className="w-10 h-10 rounded-xl bg-teal-500/10 flex items-center justify-center">
                                <Clock className="w-5 h-5 text-teal-400" />
                            </div>
                            <h1 className="text-3xl font-bold text-white tracking-tight">Analysis History</h1>
                        </div>
                        <p className="text-gray-400 text-sm ml-[52px]">View and manage your past diagnostic analyses.</p>
                    </div>
                    <button onClick={() => router.push('/upload')} className="btn-primary flex items-center gap-2 text-sm">
                        <Plus className="w-4 h-4" /> New Analysis
                    </button>
                </motion.div>

                {/* Table Card */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="glass-card overflow-hidden">
                    {/* Toolbar */}
                    <div className="p-4 border-b border-navy-700/50 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-navy-800/30">
                        <span className="text-sm text-gray-400">
                            {total > 0 ? `Showing ${Math.min((page - 1) * 10 + 1, total)}–${Math.min(page * 10, total)} of ${total} analyses` : 'No analyses yet'}
                        </span>
                        <div className="flex items-center gap-2">
                            <Filter className="w-4 h-4 text-gray-500" />
                            <select
                                value={filterRisk}
                                onChange={(e) => setFilterRisk(e.target.value)}
                                className="bg-navy-900/80 border border-navy-600/50 text-sm rounded-lg px-3 py-1.5 text-gray-300 outline-none focus:border-teal-500/50 transition"
                            >
                                <option value="all">All Risks</option>
                                <option value="HIGH">High Risk</option>
                                <option value="MEDIUM">Medium Risk</option>
                                <option value="LOW">Low Risk</option>
                            </select>
                        </div>
                    </div>

                    {isLoading ? (
                        <div className="p-16 flex flex-col items-center justify-center">
                            <div className="w-10 h-10 border-3 border-teal-500 border-t-transparent rounded-full animate-spin mb-4" />
                            <p className="text-sm text-gray-500">Loading history...</p>
                        </div>
                    ) : sessions.length === 0 ? (
                        <div className="p-20 text-center flex flex-col items-center">
                            <div className="w-20 h-20 rounded-2xl bg-navy-700/30 flex items-center justify-center mb-6">
                                <FolderOpen className="w-10 h-10 text-navy-600" />
                            </div>
                            <h3 className="text-xl font-semibold text-white mb-2">No analyses yet</h3>
                            <p className="text-gray-500 mb-6">Your diagnostic analysis history will appear here.</p>
                            <button onClick={() => router.push('/upload')} className="btn-primary text-sm">
                                Upload Your First Scan
                            </button>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-navy-900/30 text-gray-500 border-b border-navy-700/50">
                                    <tr>
                                        <th className="px-6 py-4 font-medium text-xs uppercase tracking-wider">Date</th>
                                        <th className="px-6 py-4 font-medium text-xs uppercase tracking-wider">Patient ID</th>
                                        <th className="px-6 py-4 font-medium text-xs uppercase tracking-wider">Risk Level</th>
                                        <th className="px-6 py-4 font-medium text-xs uppercase tracking-wider">Status</th>
                                        <th className="px-6 py-4 font-medium text-xs uppercase tracking-wider text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-navy-700/30">
                                    {sessions.map((s, i) => (
                                        <motion.tr
                                            key={s.id}
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            transition={{ delay: i * 0.03 }}
                                            className="hover:bg-white/[0.02] transition-colors group"
                                        >
                                            <td className="px-6 py-4 text-gray-300">
                                                <div>{new Date(s.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</div>
                                                <div className="text-xs text-gray-600">{new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                                            </td>
                                            <td className="px-6 py-4 text-white font-medium">{s.patient_id || <span className="text-gray-600 italic">Anonymous</span>}</td>
                                            <td className="px-6 py-4">
                                                <span className={riskBadge(s.risk_level)}>{s.risk_level || "UNKNOWN"}</span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`text-xs font-medium ${s.status === 'COMPLETED' ? 'text-emerald-400' : s.status === 'PROCESSING' ? 'text-amber-400' : 'text-gray-400'}`}>
                                                    {s.status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex justify-end gap-1 opacity-50 group-hover:opacity-100 transition-opacity">
                                                    <button onClick={() => router.push(`/results?session_id=${s.id}`)} className="p-2 text-gray-400 hover:text-teal-400 hover:bg-teal-500/10 rounded-lg transition" title="View Results">
                                                        <Eye className="w-4 h-4" />
                                                    </button>
                                                    <button onClick={() => router.push(`/chat?session_id=${s.id}`)} className="p-2 text-gray-400 hover:text-teal-400 hover:bg-teal-500/10 rounded-lg transition" title="Open Chat">
                                                        <MessageSquare className="w-4 h-4" />
                                                    </button>
                                                    <button onClick={() => handleDelete(s.id)} className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition" title="Delete">
                                                        <Trash2 className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </td>
                                        </motion.tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Pagination */}
                    {total > 10 && (
                        <div className="p-4 border-t border-navy-700/50 flex justify-between items-center bg-navy-800/30">
                            <button disabled={page === 1} onClick={() => setPage(p => p - 1)} className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-400 hover:text-white bg-navy-900/50 rounded-lg border border-navy-700/50 disabled:opacity-30 disabled:cursor-not-allowed transition">
                                <ChevronLeft className="w-4 h-4" /> Previous
                            </button>
                            <span className="text-sm text-gray-500">Page {page} of {totalPages}</span>
                            <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)} className="flex items-center gap-1 px-3 py-1.5 text-sm text-gray-400 hover:text-white bg-navy-900/50 rounded-lg border border-navy-700/50 disabled:opacity-30 disabled:cursor-not-allowed transition">
                                Next <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    )}
                </motion.div>
            </div>
        </ProtectedRoute>
    )
}
