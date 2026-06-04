/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'legal-green': {
          50: '#f0f8f4',
          100: '#e8f5e9',
          200: '#c8e6c9',
          300: '#a5d6a7',
          400: '#81c784',
          500: '#4a7c59',
          600: '#2d5a47',
          700: '#1e3a2e',
          800: '#162d24',
          900: '#0f1f19',
        },
        'legal-gold': {
          50: '#f9f6e8',
          100: '#f3edd1',
          200: '#e8db9e',
          300: '#d4af37',
          400: '#b8860b',
          500: '#9a7209',
        },
        'parchment': '#faf9f6',
        'cream': '#f5f3ef',
      },
      fontFamily: {
        'serif': ['Playfair Display', 'Georgia', 'serif'],
        'sans': ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'gradient-shift': 'gradientShift 4s ease infinite',
      },
    },
  },
  plugins: [],
}
