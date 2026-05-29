import { useState, useEffect, useRef } from 'react'
import { apiClient } from '../api/client'

export function useAnalysisStatus(taskId, sessionId) {
    const [status, setStatus] = useState("PENDING")
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)
    const [queuePosition, setQueuePosition] = useState(null)
    const [estimatedWait, setEstimatedWait] = useState(null)
    const intervalRef = useRef(null)
    
    useEffect(() => {
        if (!taskId && !sessionId) return
        
        if (sessionId && !taskId) {
            // Loading a past session directly from history
            const fetchSession = async () => {
                try {
                    const response = await apiClient.get(`/api/v1/analyze/result/${sessionId}`)
                    // If it returns a status dict instead of the result JSON
                    if (response.data.status && response.data.status !== "READY" && response.data.status !== "COMPLETED") {
                        setStatus(response.data.status)
                        setError(response.data.message || "Analysis not ready")
                    } else {
                        // The endpoint returns the result_json directly if READY
                        setResult(response.data)
                        setStatus("COMPLETED")
                    }
                } catch (err) {
                    console.error("Session fetch error:", err)
                    setError("Failed to load session results")
                }
            }
            fetchSession()
            return
        }
        
        // Polling logic for active tasks
        const poll = async () => {
            try {
                const response = await apiClient.get(`/api/v1/analyze/status/${taskId}`)
                const statusData = response.data
                
                setStatus(statusData.status)
                setQueuePosition(statusData.position_in_queue)
                setEstimatedWait(statusData.estimated_wait_seconds)
                
                if (statusData.status === "COMPLETED") {
                    const resultResponse = await apiClient.get(`/api/v1/analyze/result/${taskId}`)
                    setResult(resultResponse.data)
                    clearInterval(intervalRef.current)
                } else if (statusData.status === "FAILED") {
                    setError(statusData.error_message || "Analysis failed")
                    clearInterval(intervalRef.current)
                } else if (statusData.status === "CANCELLED") {
                    clearInterval(intervalRef.current)
                }
            } catch (err) {
                console.error("Status poll error:", err)
            }
        }
        
        poll() 
        intervalRef.current = setInterval(poll, 3000) 
        
        return () => clearInterval(intervalRef.current)
    }, [taskId, sessionId])
    
    return { status, result, error, queuePosition, estimatedWait }
}
