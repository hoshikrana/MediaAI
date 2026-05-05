'use client'
import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth/AuthContext'
import Link from 'next/link'

export default function AuthCallbackPage() {
    const searchParams = useSearchParams()
    const router = useRouter()
    const { loginWithToken } = useAuth()
    const [errorMsg, setErrorMsg] = useState(null)

    useEffect(() => {
        const processToken = async () => {
            const token = searchParams.get('token')
            const error = searchParams.get('error')

            if (error) {
                setErrorMsg(`Authentication failed: ${error}`)
                return
            }

            if (token) {
                try {
                    await loginWithToken(token)
                    // Clean URL and redirect
                    router.replace('/upload')
                } catch (err) {
                    setErrorMsg("Failed to establish secure session.")
                }
            } else {
                setErrorMsg("No authentication token provided.")
            }
        }

        processToken()
    }, [searchParams, loginWithToken, router])

    if (errorMsg) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen p-4 text-center">
                <div className="p-6 bg-red-50 border border-red-200 rounded-lg shadow-sm">
                    <h2 className="text-lg font-semibold text-red-700 mb-2">Error</h2>
                    <p className="text-red-600 mb-4">{errorMsg}</p>
                    <Link href="/login" className="px-4 py-2 text-white bg-blue-600 rounded hover:bg-blue-700 transition">
                        Return to Login
                    </Link>
                </div>
            </div>
        )
    }

    return (
        <div className="flex flex-col items-center justify-center min-h-screen">
            <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
            <p className="text-gray-600 font-medium">Securing session...</p>
        </div>
    )
}
