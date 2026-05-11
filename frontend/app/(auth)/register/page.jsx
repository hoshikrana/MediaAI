'use client'
import { useState } from 'react'
import Link from 'next/link'
import { Brain, Mail, Lock, User, ArrowRight, AlertCircle } from 'lucide-react'

export default function RegisterPage() {
    const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' })
    const [error, setError] = useState(null)
    const [success, setSuccess] = useState(false)
    const [loading, setLoading] = useState(false)

    const update = (field) => (e) => setForm(prev => ({ ...prev, [field]: e.target.value }))

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError(null)
        if (form.password !== form.confirm) {
            setError("Passwords do not match")
            return
        }
        setLoading(true)
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
            const res = await fetch(`${API_URL}/api/v1/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ full_name: form.full_name, email: form.email, password: form.password })
            })
            if (!res.ok) {
                const data = await res.json()
                throw new Error(data.message || 'Registration failed')
            }
            setSuccess(true)
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-[85vh] flex items-center justify-center px-4 relative">
            <div className="absolute inset-0 grid-bg opacity-30" />
            <div className="relative z-10 w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-400 to-teal-500 flex items-center justify-center mx-auto mb-4 shadow-lg">
                        <Brain className="w-7 h-7 text-navy-900" />
                    </div>
                    <h1 className="text-2xl font-bold text-white">Create Account</h1>
                    <p className="text-gray-400 text-sm mt-1">Get started with MedSight AI</p>
                </div>

                <div className="glass-card p-8">
                    {success ? (
                        <div className="text-center py-4">
                            <p className="text-emerald-400 font-semibold mb-2">Account created!</p>
                            <p className="text-gray-400 text-sm mb-4">In local development, you can sign in immediately.</p>
                            <Link href="/login" className="btn-primary inline-flex items-center gap-2 text-sm">Go to Login</Link>
                        </div>
                    ) : (
                        <>
                            {error && (
                                <div className="flex items-center gap-2 px-4 py-3 mb-6 bg-red-500/10 border border-red-500/20 rounded-xl">
                                    <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                                    <p className="text-sm text-red-400">{error}</p>
                                </div>
                            )}

                            <form onSubmit={handleSubmit} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Full Name</label>
                                    <div className="relative">
                                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <input type="text" value={form.full_name} onChange={update('full_name')} placeholder="John Doe" className="input-field pl-10" required />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <input type="email" value={form.email} onChange={update('email')} placeholder="you@example.com" className="input-field pl-10" required />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Password</label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <input type="password" value={form.password} onChange={update('password')} placeholder="••••••••" className="input-field pl-10" required minLength={8} />
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">Confirm Password</label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <input type="password" value={form.confirm} onChange={update('confirm')} placeholder="••••••••" className="input-field pl-10" required />
                                    </div>
                                </div>
                                <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50">
                                    {loading ? 'Creating...' : <>Create Account <ArrowRight className="w-4 h-4" /></>}
                                </button>
                            </form>

                            <div className="mt-6 text-center">
                                <p className="text-sm text-gray-500">Already have an account? <Link href="/login" className="text-teal-400 hover:text-teal-300 font-medium">Sign in</Link></p>
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
