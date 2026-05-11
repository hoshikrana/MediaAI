'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Brain, Menu, X, LogOut, Key, Settings } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth/AuthContext'

export default function Navbar() {
    const { user, isAuthenticated, logout } = useAuth()
    const pathname = usePathname()
    const [mobileOpen, setMobileOpen] = useState(false)
    const [dropdownOpen, setDropdownOpen] = useState(false)
    const [scrolled, setScrolled] = useState(false)
    const dropdownRef = useRef(null)

    useEffect(() => {
        const handler = () => setScrolled(window.scrollY > 20)
        window.addEventListener('scroll', handler)
        return () => window.removeEventListener('scroll', handler)
    }, [])

    useEffect(() => {
        const handler = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setDropdownOpen(false)
            }
        }
        document.addEventListener('mousedown', handler)
        return () => document.removeEventListener('mousedown', handler)
    }, [])

    const navLinks = [
        { name: 'Home', href: '/' },
        { name: 'Upload', href: '/upload' },
        { name: 'History', href: '/history' },
        { name: 'Architecture', href: '/about' },
    ]

    return (
        <nav className={`fixed top-0 left-0 right-0 z-50 w-full transition-all duration-300 ${
            scrolled
                ? 'bg-navy-900/90 backdrop-blur-xl border-b border-navy-700/50 shadow-lg shadow-navy-950/50'
                : 'bg-transparent border-b border-transparent'
        }`}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link href="/" className="flex items-center space-x-2.5 group">
                        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 to-teal-500 flex items-center justify-center shadow-lg group-hover:shadow-teal-500/20 transition-shadow duration-300">
                            <Brain className="w-5 h-5 text-navy-900" />
                        </div>
                        <span className="text-lg font-bold tracking-tight gradient-text">
                            MedSight AI
                        </span>
                    </Link>

                    {/* Desktop Links */}
                    <div className="hidden md:flex items-center gap-1">
                        {navLinks.map((link) => (
                            <Link
                                key={link.name}
                                href={link.href}
                                className={`px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                                    pathname === link.href
                                        ? 'text-teal-400 bg-teal-500/10'
                                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                                }`}
                            >
                                {link.name}
                            </Link>
                        ))}
                    </div>

                    {/* Desktop Auth */}
                    <div className="hidden md:flex items-center gap-3">
                        {isAuthenticated ? (
                            <div className="relative" ref={dropdownRef}>
                                <button
                                    onClick={() => setDropdownOpen(!dropdownOpen)}
                                    className="flex items-center justify-center w-9 h-9 rounded-xl bg-navy-800 hover:bg-navy-700 border border-navy-600/50 transition-all duration-200"
                                    data-testid="user-menu"
                                >
                                    <span className="text-sm font-bold text-teal-400">
                                        {user?.full_name?.charAt(0) || 'U'}
                                    </span>
                                </button>

                                {dropdownOpen && (
                                    <div className="absolute right-0 mt-2 w-56 glass-card p-1.5 shadow-2xl animate-fade-in-up" style={{ animationDuration: '0.15s' }}>
                                        <div className="px-3 py-2.5 mb-1">
                                            <p className="text-sm font-semibold text-white truncate">{user?.full_name}</p>
                                            <p className="text-xs text-gray-400 truncate">{user?.email}</p>
                                        </div>
                                        <div className="h-px bg-navy-600/50 mx-2" />
                                        <Link href="/profile" onClick={() => setDropdownOpen(false)} className="flex items-center gap-2.5 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-navy-700/50 rounded-lg transition-colors mt-1">
                                            <Settings className="w-4 h-4" /> Profile Settings
                                        </Link>
                                        <Link href="/profile/api-keys" onClick={() => setDropdownOpen(false)} className="flex items-center gap-2.5 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-navy-700/50 rounded-lg transition-colors">
                                            <Key className="w-4 h-4" /> API Keys
                                        </Link>
                                        <div className="h-px bg-navy-600/50 mx-2 my-1" />
                                        <button
                                            onClick={() => { logout(); setDropdownOpen(false); }}
                                            className="flex items-center gap-2.5 w-full px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors"
                                            data-testid="logout-button"
                                        >
                                            <LogOut className="w-4 h-4" /> Log out
                                        </button>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <>
                                <Link href="/login" className="text-sm font-medium text-gray-400 hover:text-white transition px-3 py-2">Log in</Link>
                                <Link href="/register" className="btn-primary text-sm !py-2 !px-5">Get Started</Link>
                            </>
                        )}
                    </div>

                    {/* Mobile Menu Button */}
                    <div className="md:hidden">
                        <button onClick={() => setMobileOpen(!mobileOpen)} className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/5 transition">
                            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Drawer */}
            {mobileOpen && (
                <div className="md:hidden bg-navy-900/95 backdrop-blur-xl border-t border-navy-700/50">
                    <div className="px-4 py-4 space-y-1">
                        {navLinks.map((link) => (
                            <Link
                                key={link.name}
                                href={link.href}
                                onClick={() => setMobileOpen(false)}
                                className={`block px-4 py-2.5 rounded-xl text-base font-medium transition-all ${
                                    pathname === link.href
                                        ? 'bg-teal-500/10 text-teal-400'
                                        : 'text-gray-300 hover:bg-white/5 hover:text-white'
                                }`}
                            >
                                {link.name}
                            </Link>
                        ))}
                        <div className="h-px bg-navy-700/50 my-2" />
                        {isAuthenticated ? (
                            <button onClick={() => { logout(); setMobileOpen(false); }} className="block w-full text-left px-4 py-2.5 rounded-xl text-base font-medium text-red-400 hover:bg-red-500/10 transition">
                                Log out
                            </button>
                        ) : (
                            <Link href="/login" onClick={() => setMobileOpen(false)} className="block px-4 py-2.5 rounded-xl text-base font-medium text-gray-300 hover:bg-white/5">
                                Log in
                            </Link>
                        )}
                    </div>
                </div>
            )}
        </nav>
    )
}
