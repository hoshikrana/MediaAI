'use client'
import { useState, useEffect } from 'react'
import { Database, Cpu, BrainCircuit, Activity } from 'lucide-react'
import { apiClient } from '@/lib/api/client'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'

export default function SystemStatus() {
    const [health, setHealth] = useState(null)
    const [modalOpen, setModalOpen] = useState(false)

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                const res = await apiClient.get('/api/v1/health/detailed')
                setHealth(res.data)
            } catch (err) {
                console.error("Health check failed")
            }
        }
        fetchHealth()
        const intv = setInterval(fetchHealth, 60000)
        return () => clearInterval(intv)
    }, [])

    if (!health) return null

    const statusColor = (isHealthy, isWarning) => 
        isWarning ? 'bg-yellow-500' : isHealthy ? 'bg-green-500' : 'bg-red-500'

    return (
        <>
            <div className="fixed bottom-4 right-4 bg-navy-800 border border-navy-700 rounded-full px-4 py-2 shadow-lg flex items-center gap-4 text-xs font-mono cursor-pointer hover:bg-navy-700 transition" onClick={() => setModalOpen(true)}>
                <div className="flex items-center gap-1.5" title="Database">
                    <span className={`w-2 h-2 rounded-full ${statusColor(health.components?.database?.healthy)}`} />
                    <Database className="w-3 h-3 text-gray-400" />
                </div>
                <div className="flex items-center gap-1.5" title="GPU/Compute">
                    <span className={`w-2 h-2 rounded-full ${statusColor(health.components?.gpu?.healthy)}`} />
                    <Cpu className="w-3 h-3 text-gray-400" />
                    <span className="text-gray-400">{health.components?.gpu?.vram_free_mb || 'CPU'}</span>
                </div>
                <div className="flex items-center gap-1.5" title="AI Models">
                    <span className={`w-2 h-2 rounded-full ${statusColor(health.status !== 'unhealthy', health.warnings?.length > 0)}`} />
                    <BrainCircuit className="w-3 h-3 text-gray-400" />
                </div>
                <div className="flex items-center gap-1.5" title="Task Queue">
                    <span className={`w-2 h-2 rounded-full ${statusColor(health.components?.task_queue?.healthy)}`} />
                    <Activity className="w-3 h-3 text-gray-400" />
                    <span className="text-gray-400">{health.components?.task_queue?.active || 0}</span>
                </div>
            </div>

            <Dialog open={modalOpen} onOpenChange={setModalOpen}>
                <DialogContent className="bg-navy-900 border-navy-700 text-white max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>System Health Detailed Report</DialogTitle>
                    </DialogHeader>
                    <div className="bg-black/50 p-4 rounded text-xs font-mono overflow-auto max-h-[60vh]">
                        <pre>{JSON.stringify(health, null, 2)}</pre>
                    </div>
                </DialogContent>
            </Dialog>
        </>
    )
}
