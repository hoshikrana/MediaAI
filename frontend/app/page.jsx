'use client'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Upload, Brain, FileText, Activity, MessageSquare, Database, CheckCircle, XCircle } from 'lucide-react'
import { apiClient } from '@/lib/api/client'

export default function LandingPage() {
    const [backendStatus, setBackendStatus] = useState("checking")

    useEffect(() => {
        const checkHealth = async () => {
            try {
                await apiClient.get('/api/v1/health')
                setBackendStatus("online")
            } catch (e) {
                setBackendStatus("offline")
            }
        }
        checkHealth()
    }, [])

    return (
        <div className="flex flex-col min-h-screen bg-navy-900 overflow-hidden">
            {/* HERO SECTION */}
            <section className="relative flex flex-col items-center justify-center min-h-[90vh] text-center px-4 pt-16">
                {/* CSS background nodes would go here. For brevity, using a subtle gradient. */}
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-navy-800 via-navy-900 to-navy-950 opacity-80" />
                
                <div className="relative z-10 flex flex-col items-center max-w-4xl">
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6 px-4 py-1.5 rounded-full border border-teal-500/30 bg-teal-500/10">
                        <span className="text-sm font-medium text-teal-400">🧠 AI-Powered Medical Intelligence</span>
                    </motion.div>
                    
                    <motion.h1 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white to-teal-400">
                        MedSight AI
                    </motion.h1>
                    
                    <motion.h2 initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="text-xl md:text-2xl text-gray-300 mb-8 font-light">
                        Multimodal Diagnostic Analysis
                    </motion.h2>
                    
                    <motion.p initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
                        Fusing computer vision and natural language processing to analyze chest X-rays alongside clinical notes. Providing zero-shot classifications, interactive heatmaps, and evidence-based reports.
                    </motion.p>
                    
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="flex flex-col sm:flex-row gap-4 mb-8">
                        <Link href="/upload" className="px-8 py-3 text-lg font-medium text-navy-900 bg-teal-500 rounded-lg hover:bg-teal-400 transition shadow-[0_0_15px_rgba(0,212,180,0.3)]">
                            Try the Demo →
                        </Link>
                        <Link href="/about" className="px-8 py-3 text-lg font-medium text-white border border-navy-600 rounded-lg hover:bg-navy-800 transition">
                            View Architecture
                        </Link>
                    </motion.div>

                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6 }} className="flex items-center space-x-2 text-sm text-gray-400 bg-navy-800/50 px-3 py-1 rounded-full border border-navy-700">
                        {backendStatus === "checking" && <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />}
                        {backendStatus === "online" && <CheckCircle className="w-4 h-4 text-green-500" />}
                        {backendStatus === "offline" && <XCircle className="w-4 h-4 text-red-500" />}
                        <span>Backend {backendStatus === "checking" ? "Connecting..." : backendStatus === "online" ? "Connected" : "Offline (Render Sleep)"}</span>
                    </motion.div>
                </div>
            </section>

            {/* HOW IT WORKS */}
            <section className="py-24 bg-navy-950 px-4">
                <div className="max-w-6xl mx-auto">
                    <h3 className="text-3xl font-bold text-center mb-16 text-white">How It Works</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
                        {[
                            { step: 1, icon: <Upload className="w-8 h-8 text-teal-400" />, title: "Upload Scan + Symptoms", desc: "Upload a chest X-ray and describe patient symptoms or use voice input." },
                            { step: 2, icon: <Brain className="w-8 h-8 text-teal-400" />, title: "AI Multimodal Analysis", desc: "DINOv2 anomaly detection, BioBERT NER, and MedCLIP fusion run in parallel." },
                            { step: 3, icon: <FileText className="w-8 h-8 text-teal-400" />, title: "Get Diagnostic Report", desc: "Receive heatmap visualization, entity tags, diagnosis, and downloadable PDF." }
                        ].map((item, i) => (
                            <motion.div key={i} initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: i * 0.2 }} className="flex flex-col items-center text-center">
                                <div className="w-16 h-16 rounded-full bg-navy-800 border border-navy-600 flex items-center justify-center mb-6 relative">
                                    {item.icon}
                                    <span className="absolute -top-2 -right-2 w-6 h-6 bg-teal-500 text-navy-900 font-bold rounded-full text-sm flex items-center justify-center">{item.step}</span>
                                </div>
                                <h4 className="text-xl font-semibold mb-3 text-gray-100">{item.title}</h4>
                                <p className="text-gray-400">{item.desc}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* FEATURE GRID */}
            <section className="py-24 px-4">
                <div className="max-w-6xl mx-auto">
                    <h3 className="text-3xl font-bold text-center mb-16 text-white">Platform Capabilities</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {[
                            { icon: <Activity />, title: "Anomaly Detection", desc: "Unsupervised DINOv2-based detection of imaging abnormalities." },
                            { icon: <FileText />, title: "Medical NER", desc: "BioBERT extracts diseases, symptoms, medications from clinical text." },
                            { icon: <MessageSquare />, title: "Voice Input", desc: "Whisper transcribes spoken symptoms directly into the analysis." },
                            { icon: <Brain />, title: "Multimodal Fusion", desc: "MedCLIP aligns image and text for holistic diagnosis." },
                            { icon: <Database />, title: "RAG Chatbot", desc: "Ask follow-up questions grounded in 1000+ PubMed abstracts." },
                            { icon: <FileText />, title: "PDF Reports", desc: "Download professional diagnostic reports with findings and heatmaps." }
                        ].map((feat, i) => (
                            <div key={i} className="group p-6 bg-navy-800 rounded-2xl border border-navy-600 hover:border-teal-500/50 hover:shadow-[0_0_20px_rgba(0,212,180,0.1)] transition duration-300">
                                <div className="text-teal-400 mb-4">{feat.icon}</div>
                                <h4 className="text-lg font-semibold text-white mb-2">{feat.title}</h4>
                                <p className="text-sm text-gray-400">{feat.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* TECH STACK & FOOTER */}
            <footer className="py-12 bg-navy-950 border-t border-navy-800 text-center px-4">
                <div className="flex flex-wrap justify-center gap-3 mb-10 max-w-4xl mx-auto">
                    {["PyTorch", "HuggingFace", "BioBERT", "DINOv2", "MedCLIP", "BioGPT", "FastAPI", "Next.js", "ChromaDB"].map(tech => (
                        <span key={tech} className="px-3 py-1 bg-navy-900 border border-teal-500/30 rounded-full text-xs font-mono text-gray-300">{tech}</span>
                    ))}
                </div>
                <p className="text-xs text-gray-500 max-w-2xl mx-auto">
                    MedSight AI is a research and educational project. Not intended for clinical use. Always consult a licensed healthcare professional for medical decisions.
                </p>
            </footer>
        </div>
    )
}
