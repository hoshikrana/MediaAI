import { Inter } from "next/font/google"
import { AuthProvider } from "@/lib/auth/AuthContext"
import { Toaster } from "@/components/ui/toaster"
import Navbar from "@/components/shared/Navbar"
import "./globals.css" // Ensure this exists

const inter = Inter({ subsets: ["latin"] })

export const metadata = {
    title: { template: "%s | MedSight AI", default: "MedSight AI" },
    description: "Multimodal AI-powered medical diagnostic assistance",
    keywords: ["medical AI", "chest X-ray", "diagnostic", "radiology"],
    authors: [{ name: "MedSight AI Team" }],
    robots: "noindex"  // don't index — research project
}

export default function RootLayout({ children }) {
    return (
        <html lang="en" className="dark">
            <body className={`${inter.className} bg-navy-900 text-white min-h-screen`}>
                <AuthProvider>
                    <Navbar />
                    <main className="pt-16">
                        {children}
                    </main>
                    <Toaster />
                </AuthProvider>
            </body>
        </html>
    )
}
