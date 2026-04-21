/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
        display: ['"Cormorant Garamond"', 'Georgia', 'serif'],
      },
      colors: {
        surface: {
          DEFAULT: '#0a0f1a',
          card: '#111827',
          hover: '#1f2937',
          border: '#1e293b',
        },
        // Arquimedes — product accent (indigo)
        accent: {
          DEFAULT: '#6366f1',
          hover: '#818cf8',
          muted: '#4338ca',
          subtle: 'rgba(99, 102, 241, 0.1)',
        },
        // Mouts IT — the path / recruiter (emerald)
        mouts: {
          DEFAULT: '#10b981',
          hover: '#34d399',
          muted: '#047857',
          subtle: 'rgba(16, 185, 129, 0.12)',
        },
        // AmBev — the destination / client (warm gold)
        ambev: {
          DEFAULT: '#f59e0b',
          hover: '#fbbf24',
          muted: '#b45309',
          subtle: 'rgba(245, 158, 11, 0.12)',
        },
        text: {
          primary: '#f1f5f9',
          secondary: '#94a3b8',
          muted: '#64748b',
        },
      },
      animation: {
        'pulse-dot': 'pulse-dot 1.4s ease-in-out infinite',
        'fade-in': 'fade-in 0.4s ease-out forwards',
        'shimmer': 'shimmer 2.8s linear infinite',
        'glow': 'glow 3.4s ease-in-out infinite',
      },
      keyframes: {
        'pulse-dot': {
          '0%, 80%, 100%': { opacity: '0.3', transform: 'scale(0.8)' },
          '40%': { opacity: '1', transform: 'scale(1)' },
        },
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'glow': {
          '0%, 100%': { filter: 'drop-shadow(0 0 6px rgba(99, 102, 241, 0.4))' },
          '50%': { filter: 'drop-shadow(0 0 16px rgba(99, 102, 241, 0.7))' },
        },
      },
      backgroundImage: {
        'brand-gradient':
          'linear-gradient(90deg, rgba(16,185,129,0.15) 0%, rgba(99,102,241,0.12) 50%, rgba(245,158,11,0.15) 100%)',
        'hero-glow':
          'radial-gradient(circle at 30% 30%, rgba(99,102,241,0.35), transparent 55%), radial-gradient(circle at 70% 70%, rgba(245,158,11,0.25), transparent 60%)',
      },
    },
  },
  plugins: [],
};
