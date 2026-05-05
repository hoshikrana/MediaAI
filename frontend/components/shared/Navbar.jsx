'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Brain, Menu, X, User as UserIcon } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '@/lib/auth/AuthContext'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

export default function Navbar() {
    const { user, isAuthenticated, logout } = useAuth()
    const pathname = usePathname()
    const [mobileOpen, setMobileOpen] = useState(false)

    const navLinks = [
        { name: 'Home', href: '/' },
        { name: 'Upload', href: '/upload' },
        { name: 'History', href: '/history' },
        { name: 'About', href: '/about' },
    ]

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 w-full border-b border-navy-700 bg-navy-900/80 backdrop-blur-md">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between h-16">
                    {/* Logo */}
                    <Link href="/" className="flex items-center space-x-2">
                        <Brain className="w-8 h-8 text-teal-500" />
                        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-teal-400">
                            MedSight AI
                        </span>
                    </Link>

                    {/* Desktop Links */}
                    <div className="hidden md:flex items-center space-x-8">
                        {navLinks.map((link) => (
                            <Link 
                                key={link.name} 
                                href={link.href}
                                className={`text-sm font-medium transition-colors hover:text-teal-400 ${
                                    pathname === link.href ? 'text-teal-500 border-b-2 border-teal-500 pb-1' : 'text-gray-300'
                                }`}
                            >
                                {link.name}
                            </Link>
                        ))}
                    </div>

                    {/* Desktop Auth */}
                    <div className="hidden md:flex items-center space-x-4">
                        {isAuthenticated ? (
                            <DropdownMenu>
                                <DropdownMenuTrigger className="focus:outline-none" data-testid="user-menu">
                                    <div className="flex items-center justify-center w-9 h-9 rounded-full bg-navy-700 hover:bg-navy-600 border border-navy-600 transition" data-testid="navbar-user">
                                        <span className="text-sm font-medium text-teal-400">
                                            {user?.full_name?.charAt(0) || 'U'}
                                        </span>
                                    </div>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end" className="w-56 bg-navy-800 border-navy-600 text-white">
                                    <DropdownMenuLabel className="font-normal">
                                        <div className="flex flex-col space-y-1">
                                            <p className="text-sm font-medium leading-none">{user?.full_name}</p>
                                            <p className="text-xs leading-none text-gray-400">{user?.email}</p>
                                        </div>
                                    </DropdownMenuLabel>
                                    <DropdownMenuSeparator className="bg-navy-700" />
                                    <DropdownMenuItem className="cursor-pointer hover:bg-navy-700" asChild>
                                        <Link href="/profile">Profile Settings</Link>
                                    </DropdownMenuItem>
                                    <DropdownMenuItem className="cursor-pointer hover:bg-navy-700" asChild>
                                        <Link href="/profile/api-keys">API Keys</Link>
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator className="bg-navy-700" />
                                    <DropdownMenuItem className="cursor-pointer text-red-400 hover:bg-navy-700 hover:text-red-300" onClick={logout} data-testid="logout-button">
                                        Log out
                                    </DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                        ) : (
                            <>
                                <Link href="/login" className="text-sm font-medium text-gray-300 hover:text-white transition">Log in</Link>
                                <Link href="/register" className="px-4 py-2 text-sm font-medium text-navy-900 bg-teal-500 rounded hover:bg-teal-400 transition">Get Started</Link>
                            </>
                        )}
                    </div>

                    {/* Mobile Menu Button */}
                    <div className="md:hidden flex items-center">
                        <button onClick={() => setMobileOpen(!mobileOpen)} className="text-gray-300 hover:text-white">
                            {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Drawer */}
            {mobileOpen && (
                <div className="md:hidden bg-navy-800 border-b border-navy-700">
                    <div className="px-2 pt-2 pb-3 space-y-1">
                        {navLinks.map((link) => (
                            <Link
                                key={link.name}
                                href={link.href}
                                onClick={() => setMobileOpen(false)}
                                className={`block px-3 py-2 rounded-md text-base font-medium ${
                                    pathname === link.href ? 'bg-navy-700 text-teal-400' : 'text-gray-300 hover:bg-navy-700 hover:text-white'
                                }`}
                            >
                                {link.name}
                            </Link>
                        ))}
                        {isAuthenticated ? (
                            <button onClick={() => { logout(); setMobileOpen(false); }} className="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-red-400 hover:bg-navy-700">
                                Log out
                            </button>
                        ) : (
                            <Link href="/login" onClick={() => setMobileOpen(false)} className="block px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:bg-navy-700">
                                Log in
                            </Link>
                        )}
                    </div>
                </div>
            )}
        </nav>
    )
}
