'use client'
import { useState, useRef, useEffect } from 'react'
import { useAuth } from '@/lib/auth/AuthContext'
import { Send, Bot, User, Loader2 } from 'lucide-react'

const createId = () => (
    typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(16).slice(2)}`
)

export default function ChatInterface({ sessionId }) {
    const { accessToken } = useAuth()
    const [messages, setMessages] = useState([
        { id: 'welcome', role: 'assistant', content: "Hello! I'm the MedSight AI assistant. Ask me anything about your analysis results — I'll do my best to help explain the findings.", isStreaming: false, sources: [] }
    ])
    const [inputText, setInputText] = useState("")
    const [streamingMessageId, setStreamingMessageId] = useState(null)
    const messagesEndRef = useRef(null)

    // Fetch chat history on mount
    useEffect(() => {
        if (!sessionId || !accessToken) return;
        
        const fetchHistory = async () => {
            try {
                const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const response = await fetch(`${API_URL}/api/v1/chat/${sessionId}`, {
                    headers: { 'Authorization': `Bearer ${accessToken}` }
                });
                if (response.ok) {
                    const data = await response.json();
                    if (data && data.length > 0) {
                        setMessages([
                            { id: 'welcome', role: 'assistant', content: "Hello! I'm the MedSight AI assistant. Ask me anything about your analysis results — I'll do my best to help explain the findings.", isStreaming: false, sources: [] },
                            ...data
                        ]);
                    }
                }
            } catch (err) {
                console.error("Failed to fetch chat history:", err);
            }
        };
        fetchHistory();
    }, [sessionId, accessToken]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const sendMessage = async (e) => {
        e.preventDefault()
        if(!inputText.trim() || streamingMessageId) return
        
        const text = inputText
        setInputText("")
        
        const userMsg = { id: createId(), role: "user", content: text }
        setMessages(prev => [...prev, userMsg])
        
        const assistantMsgId = createId()
        const assistantMsg = { id: assistantMsgId, role: "assistant", content: "", isStreaming: true, sources: [] }
        setMessages(prev => [...prev, assistantMsg])
        setStreamingMessageId(assistantMsgId)
        
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        
        try {
            const response = await fetch(`${API_URL}/api/v1/chat`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json", 
                    "Authorization": `Bearer ${accessToken}` 
                },
                credentials: "include",
                body: JSON.stringify({ session_id: sessionId, message: text })
            })

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}))
                throw new Error(errData.message || errData.detail || `Server error: ${response.status}`)
            }
            
            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let buffer = ""
            
            while (true) {
                const { done, value } = await reader.read()
                if (done) break
                
                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split("\n\n")
                buffer = lines.pop() // keep incomplete chunk
                
                for (const line of lines) {
                    const trimmed = line.trim()
                    if (!trimmed.startsWith("data: ")) continue
                    
                    try {
                        const data = JSON.parse(trimmed.replace("data: ", ""))
                        
                        if (data.type === "token") {
                            setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content: m.content + data.token } : m))
                        } else if (data.type === "sources") {
                            setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, sources: data.sources } : m))
                        } else if (data.type === "done") {
                            setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, isStreaming: false } : m))
                            setStreamingMessageId(null)
                        }
                    } catch (parseErr) {
                        // skip malformed SSE chunk
                    }
                }
            }
            // If stream ended without a "done" event
            setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, isStreaming: false } : m))
            setStreamingMessageId(null)
        } catch (error) {
            console.error("Chat error:", error)
            setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content: `Error: ${error.message || "Failed to connect"}`, isStreaming: false } : m))
            setStreamingMessageId(null)
        }
    }

    return (
        <div className="flex flex-col h-full">
            {/* Messages area */}
            <div className="flex-1 p-4 overflow-y-auto space-y-4">
                {messages.map(m => (
                    <div key={m.id} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        {m.role === 'assistant' && (
                            <div className="w-8 h-8 rounded-lg bg-teal-500/20 border border-teal-500/30 flex items-center justify-center shrink-0 mt-1">
                                <Bot className="w-4 h-4 text-teal-400" />
                            </div>
                        )}
                        <div className={`max-w-[80%] p-3 rounded-xl text-sm leading-relaxed ${
                            m.role === 'user' 
                                ? 'bg-teal-600 text-white rounded-br-sm' 
                                : 'bg-navy-700/80 text-gray-200 border border-navy-600 rounded-bl-sm'
                        }`}>
                            <p className="whitespace-pre-wrap">{m.content}</p>
                            {m.isStreaming && <span className="inline-block w-2 h-4 ml-1 bg-teal-400 animate-pulse rounded-sm" />}
                            {m.sources?.length > 0 && (
                                <div className="mt-3 pt-2 border-t border-navy-600/50 text-xs text-gray-400">
                                    <p className="font-semibold mb-1 text-gray-300">Sources:</p>
                                    {m.sources.map((s, i) => (
                                        <p key={i} className="truncate">• {s.title?.substring(0, 60) || 'Medical reference'}...</p>
                                    ))}
                                </div>
                            )}
                        </div>
                        {m.role === 'user' && (
                            <div className="w-8 h-8 rounded-lg bg-navy-600 border border-navy-500 flex items-center justify-center shrink-0 mt-1">
                                <User className="w-4 h-4 text-gray-300" />
                            </div>
                        )}
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input area */}
            <form onSubmit={sendMessage} className="p-3 border-t border-navy-700 bg-navy-900/50 flex items-center gap-2">
                <input
                    type="text"
                    value={inputText}
                    onChange={e => setInputText(e.target.value)}
                    disabled={!!streamingMessageId}
                    className="flex-1 px-4 py-2.5 bg-navy-700/50 border border-navy-600 rounded-lg text-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500/50 disabled:opacity-50 transition"
                    placeholder="Ask about the analysis results..."
                />
                <button 
                    type="submit" 
                    disabled={!!streamingMessageId || !inputText.trim()} 
                    className="p-2.5 bg-teal-600 text-white rounded-lg hover:bg-teal-500 disabled:opacity-30 disabled:cursor-not-allowed transition shrink-0"
                >
                    {streamingMessageId ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </button>
            </form>
        </div>
    )
}
