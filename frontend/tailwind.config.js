/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // 主色调（蓝色系）
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        // 浅色主题配色
        light: {
          bg: '#f8fafc',
          surface: '#ffffff',
          border: '#e2e8f0',
          text: '#1e293b',
          muted: '#64748b',
          secondary: '#f1f5f9'
        },
        // 深色主题配色（保留用于未来扩展）
        dark: {
          bg: '#0a0a0f',
          surface: '#13131a',
          border: '#1f1f2e',
          text: '#e4e4e7',
          muted: '#71717a'
        },
        // 新增：语义化颜色
        success: {
          500: '#22c55e',
          600: '#16a34a'
        },
        warning: {
          500: '#f59e0b',
          600: '#d97706'
        },
        danger: {
          500: '#ef4444',
          600: '#dc2626'
        }
      },
      backdropBlur: {
        xs: '2px',
        sm: '4px',
        md: '8px',
        lg: '12px',
        xl: '16px'
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'typewriter': 'typewriter 0.05s steps(1, end)'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' }
        },
        typewriter: {
          '0%, 100%': { opacity: '1' }
        }
      }
    }
  }
}
