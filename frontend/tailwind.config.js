/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
    './app/**/*.{js,jsx}',
    './src/**/*.{js,jsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        navy: {
          950: "#050D1A",
          900: "#0A1628",
          800: "#0F2040",
          700: "#162B55",
          600: "#1E3A6E",
          500: "#2A4D87",
          400: "#3A6AAE"
        },
        teal: {
          400: "#00F5D4",
          500: "#00D4B4",
          600: "#00B39A",
        },
        risk: {
          high: "#FF4444",
          medium: "#FFB347",
          low: "#44FF88"
        },
        // Shadcn UI required colors (mapped to our theme)
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "#0A1628",
        foreground: "#ffffff",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"]
      },
      keyframes: {
        "pulse-ring": {
          "0%": { transform: "scale(0.8)", opacity: "0.5" },
          "100%": { transform: "scale(1.3)", opacity: "0" },
        },
        "typewriter": {
          to: { left: "100%" }
        },
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        }
      },
      animation: {
        "pulse-ring": "pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "typewriter": "typewriter 0.05s steps(1) forwards",
        "fade-up": "fade-up 0.5s ease-out"
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
