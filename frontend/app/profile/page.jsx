'use client'
import { useEffect, useState } from 'react'
import { Save, User, Mail, AlertCircle, CheckCircle2 } from 'lucide-react'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { apiClient } from '@/lib/api/client'
import { useAuth } from '@/lib/auth/AuthContext'

export default function ProfilePage() {
    const { user, refreshAccessToken } = useAuth()
    const [fullName, setFullName] = useState('')
    const [profilePictureUrl, setProfilePictureUrl] = useState('')
    const [status, setStatus] = useState(null)
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        if (user) {
            setFullName(user.full_name || '')
            setProfilePictureUrl(user.profile_picture_url || '')
        }
    }, [user])

    const saveProfile = async (e) => {
        e.preventDefault()
        setLoading(true)
        setStatus(null)
        try {
            await apiClient.patch('/api/v1/users/me', {
                full_name: fullName,
                profile_picture_url: profilePictureUrl || null,
            })
            await refreshAccessToken()
            setStatus({ type: 'success', message: 'Profile updated.' })
        } catch (err) {
            setStatus({ type: 'error', message: err.response?.data?.message || 'Could not update profile.' })
        } finally {
            setLoading(false)
        }
    }

    return (
        <ProtectedRoute>
            <div className="max-w-3xl mx-auto px-4 py-10">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-white">Profile Settings</h1>
                    <p className="text-gray-400 mt-2">Manage the account used for analyses, reports, and API keys.</p>
                </div>

                <form onSubmit={saveProfile} className="glass-card p-6 space-y-5">
                    {status && (
                        <div className={`flex items-center gap-2 px-4 py-3 rounded-xl border ${status.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300' : 'bg-red-500/10 border-red-500/20 text-red-300'}`}>
                            {status.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                            <p className="text-sm">{status.message}</p>
                        </div>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                            <input value={user?.email || ''} disabled className="input-field pl-10 opacity-70" />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Full Name</label>
                        <div className="relative">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                            <input value={fullName} onChange={(e) => setFullName(e.target.value)} className="input-field pl-10" minLength={2} required />
                        </div>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Profile Image URL</label>
                        <input value={profilePictureUrl} onChange={(e) => setProfilePictureUrl(e.target.value)} className="input-field" placeholder="https://example.com/avatar.png" />
                    </div>

                    <button disabled={loading} className="btn-primary flex items-center gap-2 disabled:opacity-60">
                        <Save className="w-4 h-4" /> {loading ? 'Saving...' : 'Save Changes'}
                    </button>
                </form>
            </div>
        </ProtectedRoute>
    )
}
