'use client'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth/AuthContext'

export default function PublicOnlyRoute({ children }) {
    const { isAuthenticated, isLoading } = useAuth()
    const router = useRouter()

    useEffect(() => {
        if (!isLoading && isAuthenticated) {
            router.push('/upload')
        }
    }, [isLoading, isAuthenticated, router])

    if (isLoading) return null

    return !isAuthenticated ? children : null
}
