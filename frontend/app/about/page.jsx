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
        { component: "Feature Backbone", id: "VGG16 (ImageNet, frozen)", size: "~528MB", device: "CPU/GPU", deviceColor: "text-purple-400", purpose: "Frozen 512-d feature extraction from chest X-rays" },
        { component: "VAE (Encoder + Decoder)", id: "Custom (trained)", size: "~5MB", device: "CPU/GPU", deviceColor: "text-purple-400", purpose: "Learns 256-d latent manifold of normal anatomy (1.32M params)" },
        { component: "ViT Anomaly Scorer", id: "Custom (trained)", size: "~5MB", device: "CPU/GPU", deviceColor: "text-purple-400", purpose: "6-layer, 8-head transformer scoring latent patches (1.21M params)" },
        { component: "Clinical NER", id: "en_core_sci_sm (scispaCy)", size: "~15MB", device: "CPU", deviceColor: "text-blue-400", purpose: "Medical entity extraction: diseases, symptoms, medications" },
        { component: "Zero-Shot Classifier", id: "valhalla/distilbart-mnli-12-1", size: "~300MB", device: "CPU", deviceColor: "text-blue-400", purpose: "Classifies clinical text across 20 pulmonary conditions" },
        { component: "RAG Embedder", id: "sentence-transformers/all-MiniLM-L6-v2", size: "~80MB", device: "CPU", deviceColor: "text-blue-400", purpose: "384-d semantic embeddings for PubMed retrieval" },
        { component: "Report Generation", id: "microsoft/biogpt", size: "~700MB", device: "CPU", deviceColor: "text-blue-400", purpose: "PubMed-grounded medical text generation" },
    ]

    const metrics = [
        { label: "Anomaly Detection AUROC", value: "0.718", icon: <Activity className="w-5 h-5" /> },
        { label: "ViT Validation Accuracy", value: "98.6%", icon: <Layers className="w-5 h-5" /> },
        { label: "Total Trainable Parameters", value: "2.53M", icon: <Zap className="w-5 h-5" /> },
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
                    A multimodal medical diagnostic platform using a novel <strong className="text-white">VGG16 → VAE → Vision Transformer</strong> pipeline for unsupervised pulmonary anomaly detection. Trained exclusively on normal chest X-rays from the COVID-19 Radiography Database (21,165 images). Achieves <strong className="text-teal-400">AUROC 0.718</strong> with only <strong className="text-teal-400">2.53M trainable parameters</strong> under 4GB VRAM.
                </p>
            </motion.section>

            {/* PIPELINE DIAGRAM */}
            <motion.section initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="glass-card p-8 overflow-hidden">
                <h2 className="text-2xl font-bold text-white mb-8 text-center">Three-Stage Vision Pipeline</h2>
                <div className="relative w-full max-w-4xl mx-auto aspect-[16/9] flex items-center justify-center">
                    <svg viewBox="0 0 900 450" className="w-full h-full drop-shadow-lg font-sans">
                        <defs>
                            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                                <polygon points="0 0, 10 3.5, 0 7" fill="#00D4B4" />
                            </marker>
                            <marker id="arrowAmber" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                                <polygon points="0 0, 10 3.5, 0 7" fill="#FFB347" />
                            </marker>
                            <linearGradient id="boxGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="0%" stopColor="#1E3A6E" />
                                <stop offset="100%" stopColor="#0F2040" />
                            </linearGradient>
                        </defs>

                        {/* Stage 1 */}
                        <rect x="30" y="160" width="130" height="65" rx="10" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="1.5" />
                        <text x="95" y="186" fill="white" textAnchor="middle" fontSize="14" fontWeight="700">X-ray</text>
                        <text x="95" y="206" fill="#8899aa" textAnchor="middle" fontSize="11">224×224×3</text>

                        <rect x="200" y="160" width="140" height="65" rx="10" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="1.5" />
                        <text x="270" y="186" fill="white" textAnchor="middle" fontSize="13" fontWeight="600">VGG16</text>
                        <text x="270" y="206" fill="#8899aa" textAnchor="middle" fontSize="10">Frozen · ImageNet</text>

                        {/* Stage 2 */}
                        <rect x="380" y="140" width="160" height="100" rx="12" fill="url(#boxGradient)" stroke="#FFB347" strokeWidth="2" />
                        <text x="460" y="172" fill="white" textAnchor="middle" fontSize="14" fontWeight="700">VAE</text>
                        <text x="460" y="192" fill="#FFB347" textAnchor="middle" fontSize="11">512→256→512</text>
                        <text x="460" y="210" fill="#8899aa" textAnchor="middle" fontSize="10">1.32M params</text>
                        <text x="460" y="230" fill="#8899aa" textAnchor="middle" fontSize="10">β = 0.001</text>

                        {/* Stage 3 */}
                        <rect x="590" y="140" width="160" height="100" rx="12" fill="url(#boxGradient)" stroke="#FF6B6B" strokeWidth="2" />
                        <text x="670" y="172" fill="white" textAnchor="middle" fontSize="14" fontWeight="700">ViT Scorer</text>
                        <text x="670" y="192" fill="#FF6B6B" textAnchor="middle" fontSize="11">6 layers · 8 heads</text>
                        <text x="670" y="210" fill="#8899aa" textAnchor="middle" fontSize="10">1.21M params</text>
                        <text x="670" y="230" fill="#8899aa" textAnchor="middle" fontSize="10">d=128 · 8 patches</text>

                        {/* Output */}
                        <rect x="790" y="165" width="95" height="55" rx="10" fill="url(#boxGradient)" stroke="#44FF88" strokeWidth="1.5" />
                        <text x="837" y="190" fill="#44FF88" textAnchor="middle" fontSize="13" fontWeight="700">Score</text>
                        <text x="837" y="206" fill="#8899aa" textAnchor="middle" fontSize="10">[0, 100]</text>

                        {/* Arrows main pipeline */}
                        <line x1="160" y1="192" x2="195" y2="192" stroke="#00D4B4" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
                        <line x1="340" y1="192" x2="375" y2="192" stroke="#00D4B4" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
                        <line x1="540" y1="192" x2="585" y2="192" stroke="#FFB347" strokeWidth="1.5" markerEnd="url(#arrowAmber)" />
                        <line x1="750" y1="192" x2="785" y2="192" stroke="#44FF88" strokeWidth="1.5" markerEnd="url(#arrowhead)" />

                        {/* Dimension labels on arrows */}
                        <text x="275" y="155" fill="#5588aa" textAnchor="middle" fontSize="10" fontStyle="italic">512-d</text>
                        <text x="460" y="130" fill="#5588aa" textAnchor="middle" fontSize="10" fontStyle="italic">256-d latent z</text>

                        {/* Anomaly signal branches */}
                        <text x="460" y="280" fill="#FFB347" textAnchor="middle" fontSize="10">Recon. Error (40%)</text>
                        <text x="460" y="300" fill="#FFB347" textAnchor="middle" fontSize="10">KL Divergence (20%)</text>
                        <text x="670" y="280" fill="#FF6B6B" textAnchor="middle" fontSize="10">ViT Score (40%)</text>

                        <path d="M 460 240 L 460 265" fill="none" stroke="#FFB347" strokeWidth="1" strokeDasharray="4,3" />
                        <path d="M 670 240 L 670 265" fill="none" stroke="#FF6B6B" strokeWidth="1" strokeDasharray="4,3" />

                        {/* NLP Side */}
                        <rect x="30" y="350" width="130" height="55" rx="10" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="1.5" />
                        <text x="95" y="374" fill="white" textAnchor="middle" fontSize="12" fontWeight="600">Clinical Notes</text>
                        <text x="95" y="392" fill="#8899aa" textAnchor="middle" fontSize="10">Text / Voice</text>

                        <rect x="200" y="350" width="140" height="55" rx="10" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="1.5" />
                        <text x="270" y="374" fill="white" textAnchor="middle" fontSize="12">scispaCy NER</text>
                        <text x="270" y="392" fill="#8899aa" textAnchor="middle" fontSize="10">+ DistilBART</text>

                        <rect x="380" y="350" width="160" height="55" rx="10" fill="url(#boxGradient)" stroke="#44FF88" strokeWidth="1.5" />
                        <text x="460" y="374" fill="white" textAnchor="middle" fontSize="12">RAG Chatbot</text>
                        <text x="460" y="392" fill="#8899aa" textAnchor="middle" fontSize="10">BioGPT + ChromaDB</text>

                        <line x1="160" y1="377" x2="195" y2="377" stroke="#00D4B4" strokeWidth="1.5" markerEnd="url(#arrowhead)" />
                        <line x1="340" y1="377" x2="375" y2="377" stroke="#00D4B4" strokeWidth="1.5" markerEnd="url(#arrowhead)" />

                        {/* Stage labels */}
                        <text x="270" y="145" fill="#00D4B4" textAnchor="middle" fontSize="11" fontWeight="700">STAGE 1</text>
                        <text x="460" y="120" fill="#FFB347" textAnchor="middle" fontSize="11" fontWeight="700">STAGE 2</text>
                        <text x="670" y="130" fill="#FF6B6B" textAnchor="middle" fontSize="11" fontWeight="700">STAGE 3</text>

                        {/* Dataset label */}
                        <rect x="30" y="30" width="250" height="45" rx="8" fill="url(#boxGradient)" stroke="#334466" strokeWidth="1" />
                        <text x="155" y="50" fill="#8899aa" textAnchor="middle" fontSize="10">COVID-19 Radiography Database</text>
                        <text x="155" y="66" fill="white" textAnchor="middle" fontSize="11" fontWeight="600">10,192 Normal · 10,973 Anomaly</text>
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
                                    <th className="px-6 py-4 font-medium text-xs uppercase tracking-wider">Model / ID</th>
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
                        *Evaluated on COVID-19 Radiography Database. VAE trained 50 epochs, ViT trained 30 epochs. Threshold = 0.348.
                    </p>
                </motion.section>

                <motion.section initial={{ opacity: 0, x: 20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} className="glass-card p-7">
                    <div className="flex items-center gap-3 mb-6">
                        <Database className="w-5 h-5 text-teal-400" />
                        <h3 className="text-lg font-bold text-white">Training Data & Setup</h3>
                    </div>
                    <ul className="space-y-4">
                        <li className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-teal-400 rounded-full mt-2 shrink-0" />
                            <div>
                                <p className="text-white font-medium text-sm">COVID-19 Radiography Database</p>
                                <p className="text-xs text-gray-400">10,192 Normal (train) · 3,616 COVID · 6,012 Lung Opacity · 1,345 Viral Pneumonia (eval only)</p>
                            </div>
                        </li>
                        <li className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-teal-400 rounded-full mt-2 shrink-0" />
                            <div>
                                <p className="text-white font-medium text-sm">Unsupervised Training</p>
                                <p className="text-xs text-gray-400">VAE trained only on normal X-rays. All pathology classes held out for evaluation. True anomaly detection.</p>
                            </div>
                        </li>
                        <li className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-teal-400 rounded-full mt-2 shrink-0" />
                            <div>
                                <p className="text-white font-medium text-sm">PubMed Abstracts (RAG)</p>
                                <p className="text-xs text-gray-400">~1,000 radiology abstracts ingested into ChromaDB for retrieval-augmented medical Q&amp;A</p>
                            </div>
                        </li>
                        <li className="flex items-start gap-3">
                            <div className="w-2 h-2 bg-amber-400 rounded-full mt-2 shrink-0" />
                            <div>
                                <p className="text-white font-medium text-sm">Resource Constraints</p>
                                <p className="text-xs text-gray-400">Designed for &lt;4GB VRAM. FP16 mixed-precision. Gradient accumulation. Memory-mapped data loading.</p>
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
                        <p className="text-sm text-gray-400">View source code and research artifacts</p>
                    </div>
                </a>
                <a href="https://huggingface.co" target="_blank" rel="noopener noreferrer" className="glass-card-hover p-6 flex items-center gap-4 group">
                    <div className="w-12 h-12 rounded-xl bg-navy-700/50 flex items-center justify-center group-hover:bg-teal-500/10 transition-colors">
                        <Server className="w-6 h-6 text-gray-400 group-hover:text-teal-400 transition" />
                    </div>
                    <div className="flex-1">
                        <h4 className="text-base font-bold text-white flex items-center gap-2">Research Paper <ExternalLink className="w-3.5 h-3.5 text-gray-500" /></h4>
                        <p className="text-sm text-gray-400">Read the full technical paper with ablation studies</p>
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
                    MedSight AI is a research and educational project. Not intended for clinical use, diagnostics, or patient treatment. Always consult a licensed healthcare professional.
                </p>
            </section>
        </div>
    )
}
