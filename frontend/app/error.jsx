'use client'
import { useEffect } from 'react'
import { Brain, AlertCircle } from 'lucide-react'
import Link from 'next/link'

export default function Error({ error, reset }) {
    useEffect(() => {
        console.error("Global Error Caught:", error)
    }, [error])

    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] text-center px-4">
            <Brain className="w-16 h-16 text-navy-700 mb-6" />
            <div className="flex items-center space-x-2 text-red-400 mb-4">
                <AlertCircle className="w-6 h-6" />
                <h2 className="text-2xl font-bold">Something went wrong!</h2>
            </div>
            <p className="text-gray-400 max-w-md mb-8">
                {error.message || "An unexpected error occurred in the application layer."}
            </p>
            <div className="flex space-x-4">
                <button
                    onClick={() => reset()}
                    className="px-6 py-2 bg-navy-700 text-white rounded hover:bg-navy-600 transition"
                >
                    Try Again
                </button>
                <Link
                    href="/"
                    className="px-6 py-2 bg-teal-600 text-white rounded hover:bg-teal-700 transition"
                >
                    Go Home
                </Link>
            </div>
        </div>
    )
}
