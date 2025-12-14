/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          accent: '#005cde',
          secondary: '#2563eb',
        },
        success: {
          DEFAULT: '#00B96B',
          light: '#4ade80',
        },
        warning: {
          DEFAULT: '#F4801A',
          light: '#eab308',
        },
        error: {
          DEFAULT: '#ef4444',
          light: '#ea5756',
        },
        dark: {
          bgPrimary: '#121212',
          bgSecondary: '#0a0a0a',
          card: '#0a0a0a',
          textPrimary: '#ffffff',
          textSecondary: '#d1d5db',
          borderLight: '#222222',
          borderMedium: '#333333',
        },
        light: {
          bgPrimary: '#ffffff',
          bgSecondary: '#f3f4f6',
          card: '#ffffff',
          textPrimary: '#111827',
          textSecondary: '#374151',
          borderLight: '#e5e7eb',
        },
      },
      borderRadius: {
        card: '12px',
        button: '4px',
        input: '4px',
        badge: '9999px',
      },
      fontFamily: {
        mono: ['var(--font-mono)', 'monospace'],
        sans: ['var(--font-sans)', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

