/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      // Design system colors from tokens
      colors: {
        // Primary brand colors
        primary: {
          50: '#E6F2FF',
          100: '#CCE5FF',
          500: '#0066FF',
          600: '#0052CC',
          900: '#003D99',
          DEFAULT: '#0066FF',
        },
        // Neutral colors
        neutral: {
          50: '#FAFAFA',
          100: '#F5F5F5',
          200: '#E5E5E5',
          500: '#A3A3A3',
          700: '#404040',
          900: '#171717',
        },
        // Semantic colors
        semantic: {
          success: '#10B981',
          warning: '#F59E0B',
          error: '#EF4444',
          info: '#3B82F6',
        },
        // Glass surfaces
        glass: {
          light: 'rgba(255, 255, 255, 0.4)',
          lightHover: 'rgba(255, 255, 255, 0.55)',
          dark: 'rgba(30, 30, 30, 0.5)',
          border: 'rgba(255, 255, 255, 0.3)',
        },
        // UI colors
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      fontFamily: {
        primary: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'Monaco', 'monospace'],
      },
      fontSize: {
        hero: ['64px', { lineHeight: '1.1', letterSpacing: '-0.02em' }],
        heroMobile: ['40px', { lineHeight: '1.1', letterSpacing: '-0.01em' }],
        title: ['48px', { lineHeight: '1.2', letterSpacing: '-0.01em' }],
        titleMobile: ['32px', { lineHeight: '1.2' }],
        subtitle: ['32px', { lineHeight: '1.3' }],
        subtitleMobile: ['24px', { lineHeight: '1.3' }],
        large: ['20px', { lineHeight: '1.6' }],
        body: ['16px', { lineHeight: '1.5' }],
        small: ['14px', { lineHeight: '1.5' }],
        caption: ['12px', { lineHeight: '1.4', letterSpacing: '0.01em' }],
      },
      spacing: {
        xs: '8px',
        sm: '16px',
        md: '24px',
        lg: '32px',
        xl: '48px',
        '2xl': '64px',
        '3xl': '96px',
        '4xl': '128px',
      },
      borderRadius: {
        sm: '8px',
        md: '12px',
        lg: '16px',
        xl: '24px',
        full: '9999px',
      },
      backdropBlur: {
        glass: '20px',
        glassStrong: '40px',
        md: '12px',
      },
      boxShadow: {
        card: '0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06)',
        cardHover: '0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05)',
        modal: '0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04)',
        glass: '0 8px 32px rgba(0, 0, 0, 0.08)',
      },
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'shimmer': 'shimmer 1.5s infinite',
        'pulse-subtle': 'pulse-subtle 2s infinite',
        'in': 'fadeIn 0.2s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-in-from-top-2': 'slideInFromTop 0.2s ease-out',
      },
      keyframes: {
        'accordion-down': {
          from: { height: 0 },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: 0 },
        },
        shimmer: {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        'pulse-subtle': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.8 },
        },
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        slideInFromTop: {
          '0%': { transform: 'translateY(-8px)', opacity: 0 },
          '100%': { transform: 'translateY(0)', opacity: 1 },
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}