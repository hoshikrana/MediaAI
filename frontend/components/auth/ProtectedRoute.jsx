'use client'
import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/lib/auth/AuthContext'

export default function ProtectedRoute({ children }) {
    const { isAuthenticated, isLoading } = useAuth()
    const router = useRouter()
    const pathname = usePathname()

    useEffect(() => {
        if (!isLoading && !isAuthenticated) {
            sessionStorage.setItem('intendedPath', pathname)
            router.push('/login')
        }
    }, [isLoading, isAuthenticated, router, pathname])

    if (isLoading) {
        return <div className="flex items-center justify-center min-h-screen">Loading secure environment...</div>
    }

    return isAuthenticated ? children : null
}
