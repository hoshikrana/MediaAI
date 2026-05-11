'use client'
import { motion } from 'framer-motion'
import { Code, Server, Database, Activity, Brain, Cpu, Layers, Zap, Shield, ExternalLink } from 'lucide-react'

const fadeUp = {
    hidden: { opacity: 0, y: 30 },
    visible: (i = 0) => ({
        opacity: 1, y: 0,
        transition: { duration: 0.5, delay: i * 0.1, ease: [0.25, 0.46, 0.45, 0.94] }
    })
}

export default function AboutPage() {
    const models = [
        { component: "Vision Backbone", id: "facebook/dinov2-small", size: "~400MB", device: "GPU", deviceColor: "text-purple-400", purpose: "Frozen feature extraction for anomaly detection" },
        { component: "Clinical NER", id: "dmis-lab/biobert-base-cased-v1.2", size: "~450MB", device: "GPU", deviceColor: "text-purple-400", purpose: "Disease, symptom, medication entity extraction" },
        { component: "Voice ASR", id: "openai/whisper-tiny", size: "~150MB", device: "CPU", deviceColor: "text-blue-400", purpose: "Real-time speech-to-text transcription" },
        { component: "Report Generation", id: "microsoft/biogpt", size: "~700MB", device: "CPU", deviceColor: "text-blue-400", purpose: "Medical narrative and report generation" },
        { component: "Image-Text Fusion", id: "microsoft/BiomedVLP-CXR-BERT", size: "~900MB", device: "GPU/CPU", deviceColor: "text-amber-400", purpose: "Cross-modal image-text alignment" },
    ]

    const metrics = [
        { label: "Anomaly Detection AUC", value: "~0.72", icon: <Activity className="w-5 h-5" /> },
        { label: "NER F1 Score (Disease)", value: "~0.81", icon: <Layers className="w-5 h-5" /> },
        { label: "Pipeline Success Rate", value: ">95%", icon: <Zap className="w-5 h-5" /> },
        { label: "Total VRAM Required", value: "<4GB", icon: <Cpu className="w-5 h-5" /> },
    ]

    return (
        <div className="max-w-6xl mx-auto px-4 py-12 space-y-20">

            {/* HERO */}
            <motion.section variants={fadeUp} initial="hidden" animate="visible" className="text-center pt-8">
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-teal-500/20 bg-teal-500/5 mb-6">
                    <Brain className="w-4 h-4 text-teal-400" />
                    <span className="text-sm font-medium text-teal-400">System Architecture</span>
                </div>
                <h1 className="text-4xl md:text-5xl font-black text-white mb-6 tracking-tight">About MedSight AI</h1>
                <p className="text-lg text-gray-400 max-w-3xl mx-auto leading-relaxed">
                    An open-source, multimodal medical diagnostic platform engineered to fuse Computer Vision and Natural Language Processing. Designed to operate under strict resource constraints (4GB VRAM) while delivering production-grade diagnostic capabilities.
                </p>
            </motion.section>

            {/* PIPELINE DIAGRAM */}
            <motion.section initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-card p-8 overflow-hidden">
                <h2 className="text-2xl font-bold text-white mb-8 text-center">Multimodal Pipeline</h2>
                <div className="relative w-full max-w-3xl mx-auto aspect-[16/9] flex items-center justify-center">
                    <svg viewBox="0 0 800 450" className="w-full h-full drop-shadow-lg font-sans">
                        <defs>
                            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                                <polygon points="0 0, 10 3.5, 0 7" fill="#00D4B4" />
                            </marker>
                            <linearGradient id="boxGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#1E3A6E" />
                                <stop offset="100%" stopColor="#0F2040" />
                            </linearGradient>
                        </defs>

                        {/* NLP Path */}
                        <rect x="50" y="50" width="140" height="50" rx="10" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="1.5" />
                        <text x="120" y="80" fill="white" textAnchor="middle" fontSize="13" fontWeight="600">Voice / Text Input</text>

                        <rect x="250" y="50" width="140" height="50" rx="10" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="1.5" />
                        <text x="320" y="80" fill="white" textAnchor="middle" fontSize="13">Whisper ASR</text>

                        <rect x="450" y="50" width="140" height="50" rx="10" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="1.5" />
                        <text x="520" y="80" fill="white" textAnchor="middle" fontSize="13">BioBERT NER</text>

                        {/* Vision Path */}
                        <rect x="50" y="200" width="140" height="50" rx="10" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="1.5" />
                        <text x="120" y="230" fill="white" textAnchor="middle" fontSize="13" fontWeight="600">Chest X-ray</text>

                        <rect x="250" y="200" width="140" height="50" rx="10" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="1.5" />
                        <text x="320" y="230" fill="white" textAnchor="middle" fontSize="13">DINOv2 Anomaly</text>

                        <rect x="450" y="200" width="140" height="50" rx="10" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="1.5" />
                        <text x="520" y="230" fill="white" textAnchor="middle" fontSize="13">Grad-CAM</text>

                        {/* Fusion */}
                        <rect x="650" y="125" width="120" height="120" rx="12" fill="url(#boxGradient)" stroke="#FFB347" strokeWidth="2" />
                        <text x="710" y="180" fill="white" textAnchor="middle" fontSize="14" fontWeight="700">MedCLIP</text>
                        <text x="710" y="200" fill="#FFB347" textAnchor="middle" fontSize="12">Fusion</text>

                        {/* RAG */}
                        <rect x="250" y="350" width="140" height="50" rx="10" fill="url(#boxGradient)" stroke="#44FF88" strokeWidth="1.5" />
                        <text x="320" y="380" fill="white" textAnchor="middle" fontSize="13">ChromaDB</text>

                        <rect x="450" y="350" width="140" height="50" rx="10" fill="url(#boxGradient)" stroke="#44FF88" strokeWidth="1.5" />
                        <text x="520" y="380" fill="white" textAnchor="middle" fontSize="13">BioGPT / RAG</text>

                        {/* Arrows */}
                        <line x1="190" y1="75" x2="240" y2="75" stroke="#00D4B4" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
                        <line x1="390" y1="75" x2="440" y2="75" stroke="#00D4B4" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
                        <line x1="190" y1="225" x2="240" y2="225" stroke="#00D4B4" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
                        <line x1="390" y1="225" x2="440" y2="225" stroke="#00D4B4" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
                        <path d="M 590 75 Q 620 75 620 100 L 620 185 L 640 185" fill="none" stroke="#FFB347" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
                        <path d="M 590 225 Q 620 225 620 200 L 620 185" fill="none" stroke="#FFB347" strokeWidth="1.5" />
                        <line x1="390" y1="375" x2="440" y2="375" stroke="#44FF88" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
                        <path d="M 590 375 Q 710 375 710 255" fill="none" stroke="#44FF88" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
                    </svg>
                </div>
            </motion.section>

            {/* MODEL SPECIFICATIONS TABLE */}
            <motion.section initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
                <p className="text-sm font-semibold text-teal-400 uppercase tracking-[0.2em] mb-3">Models</p>
                <h3 className="text-2xl font-bold text-white mb-6">Model Specifications</h3>
                <div className="glass-card overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-navy-900/30 text-gray-500 border-b border-navy-700/50">
                                <tr>
                                    <th className="px-6 py-4 font-medium text-xs uppercase tracking-wider">Component</th>
                                    <th className="px-6 py-4 font-medium text-xs uppercase tracking-wider">HuggingFace ID</th>
                                    <th className="px-6 py-4 font-medium text-xs uppercase tracking-wider">Size</th>
                                    <th className="px-6 py-4 font-medium text-xs uppercase tracking-wider">Device</th>
                                    <th className="px-6 py-4 font-medium text-xs uppercase tracking-wider">Purpose</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-navy-700/30">
                                {models.map((m, i) => (
                                    <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                                        <td className="px-6 py-4 font-semibold text-white">{m.component}</td>
                                        <td className="px-6 py-4 font-mono text-xs text-teal-400/80">{m.id}</td>
                                        <td className="px-6 py-4 text-gray-300">{m.size}</td>
                                        <td className={`px-6 py-4 font-medium ${m.deviceColor}`}>{m.device}</td>
                                        <td className="px-6 py-4 text-gray-400">{m.purpose}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </motion.section>

            {/* METRICS + DATA */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <motion.section initial={{ opacity: 0, x: -20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} className="glass-card p-7">
                    <div className="flex items-center gap-3 mb-6">
                        <Activity className="w-5 h-5 text-teal-400" />
                        <h3 className="text-lg font-bold text-white">Performance Metrics</h3>
                    </div>
                    <div className="space-y-4">
                        {metrics.map((m, i) => (
                            <div key={i} className="flex items-center justify-between p-3 bg-navy-900/30 rounded-xl border border-navy-700/30">
                                <div className="flex items-center gap-3">
                                    <div className="text-teal-400/70">{m.icon}</div>
                                    <span className="text-sm text-gray-300">{m.label}</span>
                                </div>
                                <span className="text-lg font-bold gradient-text-teal">{m.value}</span>
                            </div>
                        ))}
                    </div>
                    <p className="mt-5 text-xs text-amber-400/70 bg-amber-500/5 p-3 rounded-lg border border-amber-500/10">
                        *Metrics are approximate and based on research evaluation. Not clinically validated.
                    </p>
                </motion.section>

                <motion.section initial={{ opacity: 0, x: 20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} className="glass-card p-7">
                    <div className="flex items-center gap-3 mb-6">
                        <Database className="w-5 h-5 text-teal-400" />
                        <h3 className="text-lg font-bold text-white">Training Data</h3>
                    </div>
                    <ul className="space-y-4">
                        <li className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-teal-400 rounded-full mt-2 shrink-0" />
                            <div>
                                <p className="text-white font-medium text-sm">NIH ChestX-ray14</p>
                                <p className="text-xs text-gray-400">30,000 &quot;No Finding&quot; images for unsupervised anomaly modeling</p>
                            </div>
                        </li>
                        <li className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-teal-400 rounded-full mt-2 shrink-0" />
                            <div>
                                <p className="text-white font-medium text-sm">NCBI Disease Corpus</p>
                                <p className="text-xs text-gray-400">Fine-tuned BioBERT for medical entity recognition</p>
                            </div>
                        </li>
                        <li className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-teal-400 rounded-full mt-2 shrink-0" />
                            <div>
                                <p className="text-white font-medium text-sm">PubMed Abstracts</p>
                                <p className="text-xs text-gray-400">~1,000 radiology abstracts ingested into ChromaDB for RAG</p>
                            </div>
                        </li>
                    </ul>
                </motion.section>
            </div>

            {/* LINKS */}
            <section className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="glass-card-hover p-6 flex items-center gap-4 group">
                    <div className="w-12 h-12 rounded-xl bg-navy-700/50 flex items-center justify-center group-hover:bg-teal-500/10 transition-colors">
                        <Code className="w-6 h-6 text-gray-400 group-hover:text-teal-400 transition" />
                    </div>
                    <div className="flex-1">
                        <h4 className="text-base font-bold text-white flex items-center gap-2">GitHub Repository <ExternalLink className="w-3.5 h-3.5 text-gray-500" /></h4>
                        <p className="text-sm text-gray-400">View source code and CI/CD pipelines</p>
                    </div>
                </a>
                <a href="https://huggingface.co" target="_blank" rel="noopener noreferrer" className="glass-card-hover p-6 flex items-center gap-4 group">
                    <div className="w-12 h-12 rounded-xl bg-navy-700/50 flex items-center justify-center group-hover:bg-teal-500/10 transition-colors">
                        <Server className="w-6 h-6 text-gray-400 group-hover:text-teal-400 transition" />
                    </div>
                    <div className="flex-1">
                        <h4 className="text-base font-bold text-white flex items-center gap-2">HuggingFace Hub <ExternalLink className="w-3.5 h-3.5 text-gray-500" /></h4>
                        <p className="text-sm text-gray-400">Download trained model weights</p>
                    </div>
                </a>
            </section>

            {/* DISCLAIMER */}
            <section className="text-center pt-8 border-t border-navy-800/50">
                <div className="inline-flex items-center gap-2 mb-3">
                    <Shield className="w-4 h-4 text-gray-500" />
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Disclaimer</span>
                </div>
                <p className="text-sm text-gray-500 max-w-2xl mx-auto">
                    MedSight AI is created for software architecture demonstration, MLOps portfolio building, and educational purposes. Not intended for clinical use, diagnostics, or patient treatment. Always consult a licensed healthcare professional.
                </p>
            </section>
        </div>
    )
}
