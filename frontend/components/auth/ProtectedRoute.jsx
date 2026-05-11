'use client'
import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/lib/auth/AuthContext'

/**
 * In demo mode (no auth backend), this component renders children directly.
 * In production, it redirects unauthenticated users to /login.
 */
const DEMO_MODE = false // Auth is enforced in production

export default function ProtectedRoute({ children }) {
    const { isAuthenticated, isLoading } = useAuth()
    const router = useRouter()
    const pathname = usePathname()

    useEffect(() => {
        if (DEMO_MODE) return // Skip auth check in demo mode
        if (!isLoading && !isAuthenticated) {
            sessionStorage.setItem('intendedPath', pathname)
            router.push('/login')
        }
    }, [isLoading, isAuthenticated, router, pathname])

    // Demo mode: always render children
    if (DEMO_MODE) return children

    if (isLoading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="text-center">
                    <div className="w-10 h-10 border-3 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-sm text-gray-500">Securing environment...</p>
                </div>
            </div>
        )
    }

    return isAuthenticated ? children : null
}
