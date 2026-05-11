'use client'
import { useEffect, useState } from 'react'
import { Copy, Key, Plus, Trash2, AlertCircle } from 'lucide-react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { apiClient } from '@/lib/api/client'

export default function APIKeysPage() {
    const [keys, setKeys] = useState([])
    const [name, setName] = useState('Default key')
    const [plainKey, setPlainKey] = useState(null)
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(false)

    const loadKeys = async () => {
        const res = await apiClient.get('/api/v1/users/api-keys')
        setKeys(res.data)
    }

    useEffect(() => {
        loadKeys().catch(() => setError('Could not load API keys.'))
    }, [])

    const createKey = async (e) => {
        e.preventDefault()
        setLoading(true)
        setError(null)
        try {
            const res = await apiClient.post('/api/v1/users/api-keys', {
                name,
                permissions: ['analyze', 'chat', 'report'],
                rate_limit_per_hour: 100,
            })
            setPlainKey(res.data.plain_key)
            setName('Default key')
            await loadKeys()
        } catch (err) {
            setError(err.response?.data?.message || 'Could not create API key.')
        } finally {
            setLoading(false)
        }
    }

    const revokeKey = async (id) => {
        await apiClient.delete(`/api/v1/users/api-keys/${id}`)
        await loadKeys()
    }

    return (
        <ProtectedRoute>
            <div className="max-w-5xl mx-auto px-4 py-10">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-white">API Keys</h1>
                    <p className="text-gray-400 mt-2">Create and revoke keys for scripted access to MedSight endpoints.</p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <form onSubmit={createKey} className="glass-card p-6 space-y-4 lg:col-span-1">
                        <div className="flex items-center gap-2 text-teal-400 font-semibold">
                            <Key className="w-5 h-5" /> New Key
                        </div>
                        {error && (
                            <div className="flex items-center gap-2 text-sm text-red-300 bg-red-500/10 border border-red-500/20 rounded-xl px-3 py-2">
                                <AlertCircle className="w-4 h-4" /> {error}
                            </div>
                        )}
                        <input value={name} onChange={(e) => setName(e.target.value)} className="input-field" minLength={1} maxLength={50} />
                        <button disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-60">
                            <Plus className="w-4 h-4" /> {loading ? 'Creating...' : 'Create Key'}
                        </button>
                    </form>

                    <div className="lg:col-span-2 space-y-4">
                        {plainKey && (
                            <div className="glass-card p-5 border-teal-500/30">
                                <p className="text-sm text-teal-300 font-semibold mb-2">Copy this key now. It will not be shown again.</p>
                                <div className="flex gap-2">
                                    <code className="flex-1 bg-navy-950 border border-navy-700 rounded-lg px-3 py-2 text-xs text-gray-200 break-all">{plainKey}</code>
                                    <button onClick={() => navigator.clipboard.writeText(plainKey)} className="btn-secondary !px-3" title="Copy key">
                                        <Copy className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        )}

                        <div className="glass-card overflow-hidden">
                            <div className="p-4 border-b border-navy-700/50 text-sm font-semibold text-gray-300">Existing Keys</div>
                            {keys.length === 0 ? (
                                <p className="p-6 text-sm text-gray-500">No API keys created yet.</p>
                            ) : (
                                <div className="divide-y divide-navy-700/40">
                                    {keys.map((key) => (
                                        <div key={key.id} className="p-4 flex items-center justify-between gap-4">
                                            <div>
                                                <p className="text-white font-medium">{key.name}</p>
                                                <p className="text-xs text-gray-500">{key.key_prefix}... · {key.is_active ? 'Active' : 'Revoked'} · {key.usage_count} uses</p>
                                            </div>
                                            {key.is_active && (
                                                <button onClick={() => revokeKey(key.id)} className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg" title="Revoke key">
                                                    <Trash2 className="w-4 h-4" />
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </ProtectedRoute>
    )
}
