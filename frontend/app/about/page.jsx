'use client'
import { Code, Server, Database, Activity } from 'lucide-react'

export default function AboutPage() {
    return (
        <div className="max-w-5xl mx-auto px-4 py-12 space-y-16">
            
            {/* SECTION 1 */}
            <section className="text-center">
                <h1 className="text-4xl font-bold text-white mb-6">About MedSight AI</h1>
                <p className="text-lg text-gray-400 max-w-3xl mx-auto leading-relaxed">
                    MedSight AI is an open-source, multimodal medical diagnostic platform engineered to fuse Computer Vision and Natural Language Processing. Built to operate efficiently under strict resource constraints (4GB VRAM), it serves as a powerful educational and research tool for AI in healthcare.
                </p>
            </section>

            {/* SECTION 2: Pipeline Diagram */}
            <section className="bg-navy-800 p-8 rounded-2xl border border-navy-700 overflow-hidden">
                <h2 className="text-2xl font-semibold text-white mb-8 text-center">Multimodal Pipeline Architecture</h2>
                <div className="relative w-full max-w-3xl mx-auto aspect-[16/9] flex items-center justify-center">
                    {/* Custom SVG diagram representation */}
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
                        <rect x="50" y="50" width="140" height="50" rx="8" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="2" className="hover:opacity-80 transition cursor-pointer" />
                        <text x="120" y="80" fill="white" textAnchor="middle" fontSize="14" fontWeight="bold">Voice / Text Input</text>
                        
                        <rect x="250" y="50" width="140" height="50" rx="8" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="2" />
                        <text x="320" y="80" fill="white" textAnchor="middle" fontSize="14">Whisper ASR</text>

                        <rect x="450" y="50" width="140" height="50" rx="8" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="2" />
                        <text x="520" y="80" fill="white" textAnchor="middle" fontSize="14">BioBERT NER</text>

                        {/* Vision Path */}
                        <rect x="50" y="200" width="140" height="50" rx="8" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="2" />
                        <text x="120" y="230" fill="white" textAnchor="middle" fontSize="14" fontWeight="bold">Chest X-ray</text>

                        <rect x="250" y="200" width="140" height="50" rx="8" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="2" />
                        <text x="320" y="230" fill="white" textAnchor="middle" fontSize="14">DINOv2 Anomaly</text>

                        <rect x="450" y="200" width="140" height="50" rx="8" fill="url(#boxGradient)" stroke="#00D4B4" strokeWidth="2" />
                        <text x="520" y="230" fill="white" textAnchor="middle" fontSize="14">Grad-CAM</text>

                        {/* Fusion & Generation */}
                        <rect x="650" y="125" width="120" height="120" rx="8" fill="url(#boxGradient)" stroke="#FFB347" strokeWidth="2" />
                        <text x="710" y="180" fill="white" textAnchor="middle" fontSize="14" fontWeight="bold">MedCLIP</text>
                        <text x="710" y="200" fill="white" textAnchor="middle" fontSize="14" fontWeight="bold">Fusion</text>

                        {/* RAG Path */}
                        <rect x="250" y="350" width="140" height="50" rx="8" fill="url(#boxGradient)" stroke="#44FF88" strokeWidth="2" />
                        <text x="320" y="380" fill="white" textAnchor="middle" fontSize="14">ChromaDB (PubMed)</text>

                        <rect x="450" y="350" width="140" height="50" rx="8" fill="url(#boxGradient)" stroke="#44FF88" strokeWidth="2" />
                        <text x="520" y="380" fill="white" textAnchor="middle" fontSize="14">BioGPT / RAG</text>

                        {/* Connecting Lines */}
                        <line x1="190" y1="75" x2="240" y2="75" stroke="#00D4B4" strokeWidth="2" markerEnd="url(#arrowhead)" />
                        <line x1="390" y1="75" x2="440" y2="75" stroke="#00D4B4" strokeWidth="2" markerEnd="url(#arrowhead)" />
                        
                        <line x1="190" y1="225" x2="240" y2="225" stroke="#00D4B4" strokeWidth="2" markerEnd="url(#arrowhead)" />
                        <line x1="390" y1="225" x2="440" y2="225" stroke="#00D4B4" strokeWidth="2" markerEnd="url(#arrowhead)" />

                        {/* Merging to Fusion */}
                        <path d="M 590 75 Q 620 75 620 100 L 620 185 L 640 185" fill="none" stroke="#FFB347" strokeWidth="2" markerEnd="url(#arrowhead)" />
                        <path d="M 590 225 Q 620 225 620 200 L 620 185" fill="none" stroke="#FFB347" strokeWidth="2" />

                        {/* RAG connections */}
                        <line x1="390" y1="375" x2="440" y2="375" stroke="#44FF88" strokeWidth="2" markerEnd="url(#arrowhead)" />
                        <path d="M 590 375 Q 710 375 710 255" fill="none" stroke="#44FF88" strokeWidth="2" markerEnd="url(#arrowhead)" />
                    </svg>
                </div>
            </section>

            {/* SECTION 3: Tech Stack Table */}
            <section>
                <h3 className="text-xl font-bold text-white mb-6 border-b border-navy-700 pb-2">Model Specifications</h3>
                <div className="overflow-x-auto rounded-xl border border-navy-700">
                    <table className="w-full text-left text-sm bg-navy-800">
                        <thead className="bg-navy-900 text-teal-400">
                            <tr>
                                <th className="p-4">Model Component</th>
                                <th className="p-4">HuggingFace ID</th>
                                <th className="p-4">Size</th>
                                <th className="p-4">Device Target</th>
                                <th className="p-4">Purpose</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-navy-700 text-gray-300">
                            <tr className="hover:bg-navy-700/50">
                                <td className="p-4 font-medium text-white">Vision Backbone</td>
                                <td className="p-4 font-mono text-xs">facebook/dinov2-small</td>
                                <td className="p-4">~400MB</td>
                                <td className="p-4 text-purple-400">GPU (4GB)</td>
                                <td className="p-4">Feature extraction (Frozen)</td>
                            </tr>
                            <tr className="hover:bg-navy-700/50">
                                <td className="p-4 font-medium text-white">Clinical NER</td>
                                <td className="p-4 font-mono text-xs">dmis-lab/biobert-base-cased-v1.2</td>
                                <td className="p-4">~450MB</td>
                                <td className="p-4 text-purple-400">GPU (4GB)</td>
                                <td className="p-4">Entity extraction (Fine-tuned)</td>
                            </tr>
                            <tr className="hover:bg-navy-700/50">
                                <td className="p-4 font-medium text-white">Voice ASR</td>
                                <td className="p-4 font-mono text-xs">openai/whisper-tiny</td>
                                <td className="p-4">~150MB</td>
                                <td className="p-4 text-blue-400">CPU</td>
                                <td className="p-4">Speech-to-text</td>
                            </tr>
                            <tr className="hover:bg-navy-700/50">
                                <td className="p-4 font-medium text-white">Report Gen / Chat</td>
                                <td className="p-4 font-mono text-xs">microsoft/biogpt</td>
                                <td className="p-4">~700MB</td>
                                <td className="p-4 text-blue-400">CPU</td>
                                <td className="p-4">Medical text generation</td>
                            </tr>
                            <tr className="hover:bg-navy-700/50">
                                <td className="p-4 font-medium text-white">Image-Text Fusion</td>
                                <td className="p-4 font-mono text-xs">microsoft/BiomedVLP-CXR-BERT...</td>
                                <td className="p-4">~900MB</td>
                                <td className="p-4 text-purple-400">GPU (or CPU)</td>
                                <td className="p-4">Cross-modal alignment</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            {/* SECTION 4 & 5 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <section className="bg-navy-800 p-6 rounded-xl border border-navy-700">
                    <div className="flex items-center gap-3 mb-4">
                        <Database className="w-6 h-6 text-teal-400" />
                        <h3 className="text-xl font-bold text-white">Training Data</h3>
                    </div>
                    <ul className="space-y-3 text-gray-300 text-sm">
                        <li>• <strong>NIH ChestX-ray14:</strong> 30,000 "No Finding" images utilized for unsupervised anomaly modeling.</li>
                        <li>• <strong>NCBI Disease Corpus:</strong> Used to fine-tune BioBERT for specific medical entities.</li>
                        <li>• <strong>PubMed Abstracts:</strong> ~1,000 radiology abstracts ingested into ChromaDB for RAG context.</li>
                    </ul>
                </section>
                
                <section className="bg-navy-800 p-6 rounded-xl border border-navy-700">
                    <div className="flex items-center gap-3 mb-4">
                        <Activity className="w-6 h-6 text-teal-400" />
                        <h3 className="text-xl font-bold text-white">Performance Metrics</h3>
                    </div>
                    <ul className="space-y-3 text-gray-300 text-sm">
                        <li>• <strong>Anomaly Detection AUC:</strong> ~0.72</li>
                        <li>• <strong>NER F1 Score (Disease):</strong> ~0.81</li>
                        <li>• <strong>Pipeline Success Rate:</strong> {'>'}95%</li>
                    </ul>
                    <p className="mt-4 text-xs text-yellow-500 bg-yellow-500/10 p-2 rounded border border-yellow-500/20">
                        *Metrics are approximate. MedSight AI is a research project and has not been subjected to clinical trials.
                    </p>
                </section>
            </div>

            {/* SECTION 6: Links */}
            <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="flex items-center p-6 bg-navy-900 border border-navy-600 rounded-xl hover:border-teal-500 transition group">
                    <Code className="w-8 h-8 text-gray-400 group-hover:text-teal-400 transition mr-4" />
                    <div>
                        <h4 className="text-lg font-bold text-white">GitHub Repository</h4>
                        <p className="text-sm text-gray-400">View source code and CI/CD pipelines</p>
                    </div>
                </a>
                <a href="https://huggingface.co" target="_blank" rel="noopener noreferrer" className="flex items-center p-6 bg-navy-900 border border-navy-600 rounded-xl hover:border-teal-500 transition group">
                    <Server className="w-8 h-8 text-gray-400 group-hover:text-teal-400 transition mr-4" />
                    <div>
                        <h4 className="text-lg font-bold text-white">HuggingFace Model Hub</h4>
                        <p className="text-sm text-gray-400">Download trained model weights</p>
                    </div>
                </a>
            </section>

            {/* SECTION 7: Disclaimer */}
            <section className="text-center pt-8 border-t border-navy-800">
                <p className="text-sm text-gray-500">
                    MedSight AI is created for software architecture demonstration, MLOps portfolio building, and educational purposes. It is absolutely not intended for clinical use, diagnostics, or patient treatment. Always consult a licensed healthcare professional.
                </p>
            </section>
        </div>
    )
}
