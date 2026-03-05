/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#020617', // Slate 950
        surface: '#0f172a',    // Slate 900
        primary: {
          DEFAULT: '#06b6d4', // Cyan 500
          hover: '#0891b2',   // Cyan 600
          foreground: '#ffffff',
        },
        secondary: {
            DEFAULT: '#3b82f6', // Blue 500
            hover: '#2563eb',   // Blue 600
        },
        accent: {
          DEFAULT: '#8b5cf6', // Violet 500
          foreground: '#ffffff',
        },
        muted: {
          DEFAULT: '#1e293b', // Slate 800
          foreground: '#94a3b8', // Slate 400
        },
        border: '#1e293b', // Slate 800
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
