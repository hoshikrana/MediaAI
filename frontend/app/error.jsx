'use client'
import { useEffect } from 'react'
import { AlertCircle, RefreshCw, Home } from 'lucide-react'
import Link from 'next/link'

export default function Error({ error, reset }) {
    useEffect(() => {
        console.error("Global Error Caught:", error)
    }, [error])

    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] text-center px-4">
            <div className="glass-card p-10 max-w-md w-full">
                <div className="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center mx-auto mb-6">
                    <AlertCircle className="w-8 h-8 text-red-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Something went wrong</h2>
                <p className="text-gray-400 text-sm mb-8 leading-relaxed">
                    {error?.message || "An unexpected error occurred in the application."}
                </p>
                <div className="flex gap-3 justify-center">
                    <button
                        onClick={() => reset()}
                        className="btn-secondary flex items-center gap-2 text-sm"
                    >
                        <RefreshCw className="w-4 h-4" /> Try Again
                    </button>
                    <Link href="/" className="btn-primary flex items-center gap-2 text-sm">
                        <Home className="w-4 h-4" /> Go Home
                    </Link>
                </div>
            </div>
        </div>
    )
}
