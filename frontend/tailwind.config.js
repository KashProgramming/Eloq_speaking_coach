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
        primary: '#14B8A6',
        accent: '#FF6B6B',
        background: '#F5F1E9',
        surface: '#FAF7F2',
        textPrimary: '#1F2933',
        textSecondary: '#6B7280',
        dark: {
          background: '#0F172A',
          surface: '#1E293B',
        }
      }
    },
  },
  plugins: [],
}
