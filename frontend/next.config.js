/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    reactStrictMode: true,
    
    images: {
        domains: [],
        formats: ["image/webp", "image/avif"],
        minimumCacheTTL: 60
    },
    
    async headers() {
        return [
            {
                source: "/(.*)",
                headers: [
                    { key: "X-Frame-Options", value: "DENY" },
                    { key: "X-Content-Type-Options", value: "nosniff" },
                    { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
                    { key: "Permissions-Policy", value: "camera=(), microphone=(self), geolocation=()" },
                    {
                        key: "Content-Security-Policy",
                        value: [
                            "default-src 'self'",
                            "script-src 'self' 'unsafe-eval' 'unsafe-inline'",
                            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
                            "font-src 'self' https://fonts.gstatic.com",
                            "img-src 'self' data: blob: https:",
                            `connect-src 'self' ${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}`,
                            "frame-src 'none'",
                            "object-src 'none'"
                        ].join("; ")
                    }
                ]
            }
        ]
    },
    
    async redirects() {
        return [
            { source: "/dashboard", destination: "/upload", permanent: false }
        ]
    },
    
    env: {
        NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version || "1.0.0"
    }
}

module.exports = nextConfig
