import { Inter } from "next/font/google"
import { AuthProvider } from "@/lib/auth/AuthContext"
import { Toaster } from "@/components/ui/toaster"
import Navbar from "@/components/shared/Navbar"
import "./globals.css"

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })

export const metadata = {
    title: { template: "%s | MedSight AI", default: "MedSight AI — Multimodal Diagnostic Analysis" },
    description: "AI-powered multimodal medical diagnostic platform fusing computer vision and NLP for chest X-ray analysis, clinical NER, and evidence-based reporting.",
    keywords: ["medical AI", "chest X-ray", "diagnostic", "radiology", "deep learning", "BioBERT", "DINOv2", "MedCLIP"],
    authors: [{ name: "MedSight AI Team" }],
    robots: "noindex"
}

export default function RootLayout({ children }) {
    return (
        <html lang="en" className={`dark ${inter.variable}`}>
            <body className={`${inter.className} bg-navy-900 text-white min-h-screen antialiased`}>
                <AuthProvider>
                    <Navbar />
                    <main className="pt-16 min-h-[calc(100vh-4rem)]">
                        {children}
                    </main>
                    <Toaster />
                </AuthProvider>
            </body>
        </html>
    )
}
