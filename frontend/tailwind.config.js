/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      colors: {
        brand: {
          50:  "oklch(var(--brand-50) / <alpha-value>)",
          100: "oklch(var(--brand-100) / <alpha-value>)",
          200: "oklch(var(--brand-200) / <alpha-value>)",
          300: "oklch(var(--brand-300) / <alpha-value>)",
          400: "oklch(var(--brand-400) / <alpha-value>)",
          500: "oklch(var(--brand-500) / <alpha-value>)",
          600: "oklch(var(--brand-600) / <alpha-value>)",
          700: "oklch(var(--brand-700) / <alpha-value>)",
          800: "oklch(var(--brand-800) / <alpha-value>)",
          900: "oklch(var(--brand-900) / <alpha-value>)",
          950: "oklch(var(--brand-950) / <alpha-value>)",
        },
        dark: {
          50:  "oklch(0.9862 0.007 39.46 / <alpha-value>)",
          100: "oklch(0.9635 0.0111 3.49 / <alpha-value>)",
          200: "oklch(0.9129 0.0202 354.03 / <alpha-value>)",
          300: "oklch(0.5535 0.0345 339.86 / <alpha-value>)",
          400: "oklch(0.5224 0.035 339.96 / <alpha-value>)",
          500: "oklch(0.4887 0.0376 339.41 / <alpha-value>)",
          600: "oklch(0.4279 0.0357 335.22 / <alpha-value>)",
          700: "oklch(0.3699 0.035 332.04 / <alpha-value>)",
          800: "oklch(0.3319 0.0292 321.5 / <alpha-value>)",
          900: "oklch(0.2826 0.028 321.13 / <alpha-value>)",
          950: "oklch(0.2185 0.0171 312.79 / <alpha-value>)",
        },
        leaf: "oklch(var(--leaf) / <alpha-value>)",
        gold: "oklch(var(--gold) / <alpha-value>)",
        border: "oklch(var(--border) / <alpha-value>)",
        input: "oklch(var(--input) / <alpha-value>)",
        ring: "oklch(var(--ring) / <alpha-value>)",
        background: "oklch(var(--background) / <alpha-value>)",
        foreground: "oklch(var(--foreground) / <alpha-value>)",
        primary: {
          DEFAULT: "oklch(var(--primary) / <alpha-value>)",
          foreground: "oklch(var(--primary-foreground) / <alpha-value>)",
        },
        secondary: {
          DEFAULT: "oklch(var(--secondary) / <alpha-value>)",
          foreground: "oklch(var(--secondary-foreground) / <alpha-value>)",
        },
        destructive: {
          DEFAULT: "oklch(var(--destructive) / <alpha-value>)",
          foreground: "oklch(var(--destructive-foreground) / <alpha-value>)",
        },
        muted: {
          DEFAULT: "oklch(var(--muted) / <alpha-value>)",
          foreground: "oklch(var(--muted-foreground) / <alpha-value>)",
        },
        accent: {
          DEFAULT: "oklch(var(--accent) / <alpha-value>)",
          foreground: "oklch(var(--accent-foreground) / <alpha-value>)",
        },
        popover: {
          DEFAULT: "oklch(var(--popover) / <alpha-value>)",
          foreground: "oklch(var(--popover-foreground) / <alpha-value>)",
        },
        card: {
          DEFAULT: "oklch(var(--card) / <alpha-value>)",
          foreground: "oklch(var(--card-foreground) / <alpha-value>)",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Geist Variable", "Geist", "system-ui", "sans-serif"],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "fade-in": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-in": "fade-in 0.25s ease-out forwards",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
