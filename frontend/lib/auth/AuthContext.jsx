'use client'

import { createContext, useContext, useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { setTokenGetter } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [accessToken, setAccessToken] = useState(null)
    const [isLoading, setIsLoading] = useState(true)
    const refreshTimerRef = useRef(null)
    const router = useRouter()
    
    // Wire the API client to access our in-memory token
    useEffect(() => {
        setTokenGetter(() => accessToken)
    }, [accessToken])

    useEffect(() => {
        restoreSession()
    }, [])
    
    async function restoreSession() {
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
                method: "POST",
                credentials: "include"
            })
            if (response.ok) {
                const data = await response.json()
                setAccessToken(data.access_token)
                scheduleTokenRefresh(data.expires_in)
                await fetchUserProfile(data.access_token)
            }
        } catch (error) {
            // No valid session
        } finally {
            setIsLoading(false)
        }
    }
    
    function scheduleTokenRefresh(expiresInSeconds) {
        const refreshIn = (expiresInSeconds - 60) * 1000
        if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
        refreshTimerRef.current = setTimeout(refreshAccessToken, refreshIn)
    }
    
    async function refreshAccessToken() {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        try {
            const response = await fetch(`${API_URL}/api/v1/auth/refresh`, {
                method: "POST", credentials: "include"
            })
            if (response.ok) {
                const data = await response.json()
                setAccessToken(data.access_token)
                scheduleTokenRefresh(data.expires_in)
                await fetchUserProfile(data.access_token)
            } else {
                logout()
            }
        } catch (error) {
            logout()
        }
    }
    
    async function fetchUserProfile(token) {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${API_URL}/api/v1/auth/me`, {
            headers: { "Authorization": `Bearer ${token}` }
        })
        if (response.ok) {
            const userData = await response.json()
            setUser(userData)
        }
    }
    
    async function login(email, password) {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const formData = new FormData()
        formData.append("username", email)
        formData.append("password", password)
        
        const response = await fetch(`${API_URL}/api/v1/auth/login`, {
            method: "POST",
            body: formData,
            credentials: "include"
        })
        
        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.message || "Login failed")
        }
        
        const data = await response.json()
        setAccessToken(data.token.access_token)
        setUser(data.user)
        scheduleTokenRefresh(data.token.expires_in)
        return data
    }
    
    async function loginWithToken(token) {
        setAccessToken(token)
        scheduleTokenRefresh(30 * 60) // Assuming 30m default
        await fetchUserProfile(token)
    }
    
    async function logout() {
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        try {
            await fetch(`${API_URL}/api/v1/auth/logout`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${accessToken}` },
                credentials: "include"
            })
        } catch (e) { /* ignore network errors on logout */ }
        
        setUser(null)
        setAccessToken(null)
        if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
        router.push("/login")
    }
    
    return (
        <AuthContext.Provider value={{
            user, accessToken, isLoading,
            isAuthenticated: !!user && !!accessToken,
            login, loginWithToken, logout, refreshAccessToken
        }}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error("useAuth must be used inside AuthProvider")
    return ctx
}
