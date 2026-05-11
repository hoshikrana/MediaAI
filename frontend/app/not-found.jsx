import Link from 'next/link'
import { Brain, ArrowLeft } from 'lucide-react'

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] text-center px-4 relative">
            <div className="absolute inset-0 grid-bg opacity-30" />
            <div className="relative z-10">
                <div className="w-20 h-20 rounded-3xl bg-navy-800/80 flex items-center justify-center mx-auto mb-8 border border-navy-700/50">
                    <Brain className="w-10 h-10 text-navy-600" />
                </div>
                <h1 className="text-8xl font-black gradient-text-teal mb-4">404</h1>
                <h2 className="text-2xl font-bold text-white mb-3">Page not found</h2>
                <p className="text-gray-500 mb-10 max-w-sm mx-auto">The page you are looking for doesn&apos;t exist or has been moved.</p>
                <div className="flex gap-3 justify-center">
                    <Link href="/" className="btn-secondary flex items-center gap-2 text-sm">
                        <ArrowLeft className="w-4 h-4" /> Back to Home
                    </Link>
                    <Link href="/upload" className="btn-primary text-sm">
                        Go to Upload
                    </Link>
                </div>
            </div>
        </div>
    )
}
