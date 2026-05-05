import Link from 'next/link'
import { Brain } from 'lucide-react'

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] text-center px-4">
            <Brain className="w-20 h-20 text-navy-700 mb-6" />
            <h1 className="text-6xl font-bold text-teal-500 mb-4">404</h1>
            <h2 className="text-2xl font-semibold text-white mb-6">Page not found</h2>
            <p className="text-gray-400 mb-8">The page you are looking for doesn't exist or has been moved.</p>
            <Link
                href="/upload"
                className="px-6 py-3 bg-teal-600 text-white font-medium rounded-lg hover:bg-teal-700 transition"
            >
                Go to Upload Portal
            </Link>
        </div>
    )
}
