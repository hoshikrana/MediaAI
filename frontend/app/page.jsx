'use client'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Upload, Brain, FileText, Activity, MessageSquare, CheckCircle, XCircle, ArrowRight, Layers, Cpu } from 'lucide-react'
import { apiClient } from '@/lib/api/client'

const fadeUp = {
    hidden: { opacity: 0, y: 30 },
    visible: (i = 0) => ({
        opacity: 1,
        y: 0,
        transition: { duration: 0.6, delay: i * 0.1, ease: [0.25, 0.46, 0.45, 0.94] }
    })
}

export default function LandingPage() {
    const [backendStatus, setBackendStatus] = useState("checking")
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 })

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

    useEffect(() => {
        const handler = (e) => setMousePos({ x: e.clientX, y: e.clientY })
        window.addEventListener('mousemove', handler)
        return () => window.removeEventListener('mousemove', handler)
    }, [])

    const features = [
        { icon: <Activity className="w-6 h-6" />, title: "Unsupervised Anomaly Detection", desc: "VGG16 → VAE → ViT pipeline trained only on normal X-rays detects anomalies via reconstruction error, KL divergence, and attention-based scoring.", color: "from-red-500/20 to-red-600/5" },
        { icon: <Layers className="w-6 h-6" />, title: "ViT Attention Heatmaps", desc: "CLS token attention weights from the 6-layer Vision Transformer are upsampled to produce interpretable anomaly heatmaps.", color: "from-blue-500/20 to-blue-600/5" },
        { icon: <FileText className="w-6 h-6" />, title: "Clinical NER", desc: "scispaCy extracts diseases, symptoms, and medications. DistilBART performs zero-shot classification across 20 pulmonary conditions.", color: "from-purple-500/20 to-purple-600/5" },
        { icon: <MessageSquare className="w-6 h-6" />, title: "RAG Medical Chatbot", desc: "BioGPT generates grounded responses using PubMed abstracts retrieved via MiniLM embeddings and ChromaDB vector search.", color: "from-teal-500/20 to-teal-600/5" },
        { icon: <Brain className="w-6 h-6" />, title: "Fused Anomaly Score", desc: "Three complementary signals — reconstruction error (40%), KL divergence (20%), and ViT score (40%) — are fused into a single calibrated anomaly score.", color: "from-amber-500/20 to-amber-600/5" },
        { icon: <Cpu className="w-6 h-6" />, title: "Resource Efficient", desc: "Only 2.53M trainable parameters. Entire pipeline runs under 4GB VRAM with mixed-precision inference and VRAM-aware model registry.", color: "from-emerald-500/20 to-emerald-600/5" }
    ]

    const steps = [
        { step: 1, icon: <Upload className="w-7 h-7" />, title: "Upload & Describe", desc: "Drop a chest X-ray and add clinical notes via text or voice. scispaCy extracts medical entities automatically." },
        { step: 2, icon: <Brain className="w-7 h-7" />, title: "VGG16 → VAE → ViT", desc: "Frozen VGG16 extracts 512-d features. The VAE learns a 256-d latent manifold of normal anatomy. The ViT scores anomaly level." },
        { step: 3, icon: <FileText className="w-7 h-7" />, title: "Fused Results", desc: "Get calibrated anomaly scores, ViT attention heatmaps, NLP entity tags, risk assessment, and AI-assisted chat." }
    ]

    const techStack = ["PyTorch", "VGG16", "VAE", "Vision Transformer", "scispaCy", "DistilBART", "BioGPT", "MiniLM", "ChromaDB", "FastAPI", "Next.js"]

    const stats = [
        { value: "0.718", label: "AUROC Score" },
        { value: "2.53M", label: "Trainable Params" },
        { value: "98.6%", label: "ViT Val Accuracy" },
        { value: "21K+", label: "X-ray Dataset" }
    ]

    return (
        <div className="flex flex-col min-h-screen bg-navy-900 overflow-hidden">
            {/* ════════ HERO ════════ */}
            <section className="relative flex flex-col items-center justify-center min-h-[95vh] text-center px-4 pt-20">
                {/* Animated background */}
                <div className="absolute inset-0 grid-bg" />
                <div className="absolute inset-0 bg-gradient-to-b from-navy-900 via-transparent to-navy-900" />
                
                {/* Cursor glow */}
                <div
                    className="pointer-events-none fixed inset-0 z-30 opacity-20"
                    style={{
                        background: `radial-gradient(600px circle at ${mousePos.x}px ${mousePos.y}px, rgba(0,212,180,0.06), transparent 40%)`
                    }}
                />

                {/* Floating orbs */}
                <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-teal-500/5 rounded-full blur-3xl float" />
                <div className="absolute bottom-1/3 right-1/4 w-96 h-96 bg-teal-500/3 rounded-full blur-3xl float" style={{ animationDelay: '-3s' }} />

                <div className="relative z-10 flex flex-col items-center max-w-5xl">
                    <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0} className="mb-8">
                        <span className="inline-flex items-center gap-2 px-5 py-2 rounded-full border border-teal-500/20 bg-teal-500/5 backdrop-blur-sm">
                            <span className="w-2 h-2 bg-teal-400 rounded-full animate-pulse" />
                            <span className="text-sm font-medium text-teal-400 tracking-wide">Unsupervised Pulmonary Anomaly Detection</span>
                        </span>
                    </motion.div>

                    <motion.h1 variants={fadeUp} initial="hidden" animate="visible" custom={1} className="text-6xl md:text-8xl font-black tracking-tighter mb-4 gradient-text leading-[0.95]">
                        MedSight AI
                    </motion.h1>

                    <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={2} className="text-xl md:text-2xl text-gray-400 mb-4 font-light tracking-wide">
                        VGG16 → VAE → Vision Transformer · Multimodal Diagnostic Platform
                    </motion.p>

                    <motion.p variants={fadeUp} initial="hidden" animate="visible" custom={3} className="text-gray-500 max-w-2xl mx-auto mb-10 leading-relaxed text-base">
                        A three-stage deep learning pipeline trained exclusively on normal chest radiographs to detect pulmonary anomalies — fused with clinical NLP and a RAG-powered medical chatbot. AUROC 0.718 with only 2.53M trainable parameters.
                    </motion.p>

                    <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={4} className="flex flex-col sm:flex-row gap-4 mb-12">
                        <Link href="/upload" className="btn-primary flex items-center gap-2 text-lg">
                            Start Analysis <ArrowRight className="w-5 h-5" />
                        </Link>
                        <Link href="/about" className="btn-secondary flex items-center gap-2 text-lg">
                            View Architecture
                        </Link>
                    </motion.div>

                    {/* Status indicator */}
                    <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={5}>
                        <div className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-navy-800/60 backdrop-blur-sm border border-navy-700/60 text-sm">
                            {backendStatus === "checking" && <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />}
                            {backendStatus === "online" && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                            {backendStatus === "offline" && <XCircle className="w-4 h-4 text-red-400" />}
                            <span className="text-gray-400">
                                {backendStatus === "checking" ? "Connecting to backend..." : backendStatus === "online" ? "All systems operational" : "Backend sleeping — click to wake"}
                            </span>
                        </div>
                    </motion.div>
                </div>

                {/* Scroll indicator */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1.5 }}
                    className="absolute bottom-8 left-1/2 -translate-x-1/2"
                >
                    <div className="w-6 h-10 rounded-full border-2 border-navy-600 flex justify-center pt-2">
                        <motion.div
                            animate={{ y: [0, 8, 0] }}
                            transition={{ repeat: Infinity, duration: 1.5, ease: "easeInOut" }}
                            className="w-1.5 h-1.5 bg-teal-500 rounded-full"
                        />
                    </div>
                </motion.div>
            </section>

            {/* ════════ STATS BAR ════════ */}
            <section className="relative py-8 border-y border-navy-700/50 bg-navy-950/50 backdrop-blur-sm">
                <div className="max-w-6xl mx-auto px-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                        {stats.map((stat, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                className="text-center"
                            >
                                <p className="text-3xl md:text-4xl font-black gradient-text-teal">{stat.value}</p>
                                <p className="text-sm text-gray-500 mt-1 uppercase tracking-wider">{stat.label}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ════════ HOW IT WORKS ════════ */}
            <section className="py-28 px-4 relative">
                <div className="absolute inset-0 grid-bg opacity-50" />
                <div className="max-w-6xl mx-auto relative z-10">
                    <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-20">
                        <p className="text-sm font-semibold text-teal-400 uppercase tracking-[0.2em] mb-3">Pipeline</p>
                        <h3 className="section-title">Three-Stage Anomaly Detection</h3>
                    </motion.div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
                        {/* Connection line */}
                        <div className="hidden md:block absolute top-20 left-[20%] right-[20%] h-px bg-gradient-to-r from-transparent via-teal-500/30 to-transparent" />

                        {steps.map((item, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 40 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.15, duration: 0.5 }}
                                className="flex flex-col items-center text-center relative"
                            >
                                <div className="relative mb-8">
                                    <div className="w-16 h-16 rounded-2xl bg-navy-800 border border-navy-600 flex items-center justify-center text-teal-400 relative z-10">
                                        {item.icon}
                                    </div>
                                    <div className="absolute -top-2 -right-2 w-7 h-7 bg-gradient-to-br from-teal-400 to-teal-500 text-navy-900 font-bold rounded-lg text-sm flex items-center justify-center z-20 shadow-lg">
                                        {item.step}
                                    </div>
                                    <div className="absolute inset-0 bg-teal-500/10 rounded-2xl blur-xl" />
                                </div>
                                <h4 className="text-xl font-bold text-white mb-3">{item.title}</h4>
                                <p className="text-gray-400 leading-relaxed max-w-xs">{item.desc}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ════════ FEATURES ════════ */}
            <section className="py-28 px-4 bg-navy-950/50">
                <div className="max-w-6xl mx-auto">
                    <motion.div initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} className="text-center mb-20">
                        <p className="text-sm font-semibold text-teal-400 uppercase tracking-[0.2em] mb-3">Capabilities</p>
                        <h3 className="section-title">Built for Medical AI Research</h3>
                    </motion.div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                        {features.map((feat, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.08 }}
                                className="glass-card-hover p-6 group cursor-default"
                            >
                                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feat.color} flex items-center justify-center text-teal-400 mb-5 group-hover:scale-110 transition-transform duration-300`}>
                                    {feat.icon}
                                </div>
                                <h4 className="text-lg font-bold text-white mb-2">{feat.title}</h4>
                                <p className="text-sm text-gray-400 leading-relaxed">{feat.desc}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ════════ CTA ════════ */}
            <section className="py-28 px-4 relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-teal-500/5 via-transparent to-teal-500/5" />
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="max-w-3xl mx-auto text-center relative z-10"
                >
                    <h3 className="text-3xl md:text-5xl font-bold text-white mb-6 tracking-tight">Ready to Analyze?</h3>
                    <p className="text-gray-400 mb-10 text-lg">Upload a chest X-ray and get AI-powered diagnostic insights powered by our VGG16 → VAE → ViT anomaly detection pipeline.</p>
                    <Link href="/upload" className="btn-primary inline-flex items-center gap-2 text-lg px-10 py-4">
                        Launch Analysis <ArrowRight className="w-5 h-5" />
                    </Link>
                </motion.div>
            </section>

            {/* ════════ TECH + FOOTER ════════ */}
            <footer className="py-16 bg-navy-950 border-t border-navy-800/50 px-4">
                <div className="max-w-6xl mx-auto">
                    <div className="flex flex-wrap justify-center gap-3 mb-12">
                        {techStack.map((tech, i) => (
                            <motion.span
                                key={tech}
                                initial={{ opacity: 0, scale: 0.8 }}
                                whileInView={{ opacity: 1, scale: 1 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.05 }}
                                className="px-4 py-1.5 bg-navy-900/80 border border-navy-700/50 rounded-full text-xs font-mono text-gray-400 hover:border-teal-500/30 hover:text-teal-400 transition-all duration-300 cursor-default"
                            >
                                {tech}
                            </motion.span>
                        ))}
                    </div>

                    <div className="flex flex-col md:flex-row items-center justify-between gap-4 pt-8 border-t border-navy-800/50">
                        <div className="flex items-center gap-2">
                            <Brain className="w-5 h-5 text-teal-500" />
                            <span className="text-sm font-semibold text-gray-400">MedSight AI</span>
                        </div>
                        <p className="text-xs text-gray-600 text-center max-w-lg">
                            Research and educational project. Not intended for clinical use. Always consult a licensed healthcare professional.
                        </p>
                        <div className="flex gap-6 text-sm text-gray-500">
                            <Link href="/about" className="hover:text-teal-400 transition">Architecture</Link>
                            <Link href="/upload" className="hover:text-teal-400 transition">Upload</Link>
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    )
}
