'use client'
import { useState } from 'react'
import { v4 as uuid } from 'uuid'
import { useAuth } from '@/lib/auth/AuthContext'

export default function ChatInterface({ sessionId }) {
    const { accessToken } = useAuth()
    const [messages, setMessages] = useState([])
    const [inputText, setInputText] = useState("")
    const [streamingMessageId, setStreamingMessageId] = useState(null)

    const sendMessage = async (e) => {
        e.preventDefault()
        if(!inputText.trim() || streamingMessageId) return
        
        const text = inputText
        setInputText("")
        
        const userMsg = { id: uuid(), role: "user", content: text }
        setMessages(prev => [...prev, userMsg])
        
        const assistantMsgId = uuid()
        const assistantMsg = { id: assistantMsgId, role: "assistant", content: "", isStreaming: true, sources: [] }
        setMessages(prev => [...prev, assistantMsg])
        setStreamingMessageId(assistantMsgId)
        
        const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        
        try {
            const response = await fetch(`${API_URL}/api/v1/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "Authorization": `Bearer ${accessToken}` },
                body: JSON.stringify({ session_id: sessionId, message: text })
            })
            
            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            
            while (true) {
                const { done, value } = await reader.read()
                if (done) break
                
                const chunk = decoder.decode(value, { stream: true })
                const lines = chunk.split("\n\n").filter(l => l.startsWith("data: "))
                
                for (const line of lines) {
                    const data = JSON.parse(line.replace("data: ", ""))
                    
                    if (data.type === "token") {
                        setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content: m.content + data.token } : m))
                    } else if (data.type === "sources") {
                        setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, sources: data.sources } : m))
                    } else if (data.type === "done") {
                        setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, isStreaming: false } : m))
                        setStreamingMessageId(null)
                    }
                }
            }
        } catch (error) {
            setMessages(prev => prev.map(m => m.id === assistantMsgId ? { ...m, content: "Network error occurred.", isStreaming: false } : m))
            setStreamingMessageId(null)
        }
    }

    return (
        <div className="flex flex-col h-[600px] border rounded-lg bg-white">
            <div className="flex-1 p-4 overflow-y-auto space-y-4">
                {messages.map(m => (
                    <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] p-3 rounded-lg ${m.role === 'user' ? 'bg-teal-600 text-white' : 'bg-gray-100 text-gray-800'}`}>
                            <p>{m.content}</p>
                            {m.isStreaming && <span className="inline-block w-2 h-4 ml-1 bg-gray-400 animate-pulse" />}
                            {m.sources?.length > 0 && (
                                <div className="mt-2 pt-2 border-t border-gray-300 text-xs">
                                    <p className="font-semibold mb-1">Sources:</p>
                                    {m.sources.map((s, i) => <p key={i}>• {s.title.substring(0, 50)}...</p>)}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
            <form onSubmit={sendMessage} className="p-3 border-t bg-gray-50 flex items-center">
                <input
                    type="text"
                    value={inputText}
                    onChange={e => setInputText(e.target.value)}
                    disabled={!!streamingMessageId}
                    className="flex-1 p-2 border rounded-l-md focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:opacity-50"
                    placeholder="Ask about the results..."
                />
                <button type="submit" disabled={!!streamingMessageId} className="px-4 py-2 bg-teal-600 text-white rounded-r-md hover:bg-teal-700 disabled:opacity-50">
                    Send
                </button>
            </form>
        </div>
    )
}
