import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        hive: {
          DEFAULT: "#f5a623",
          50: "#fef8ec",
          100: "#fcedc4",
          200: "#f9d98a",
          300: "#f5c246",
          400: "#f5a623",
          500: "#e08a0a",
          600: "#c66806",
          700: "#a54909",
          800: "#87390e",
          900: "#70300f",
        },
        surface: {
          DEFAULT: "#10151d",
          deep: "#090b10",
          card: "#0d121a",
          raised: "#161d28",
          overlay: "#1b222d",
          glass: "rgba(13, 18, 26, 0.75)",
        },
        border: {
          DEFAULT: "#222d39",
          subtle: "#161e29",
          strong: "#2e3b4a",
          glass: "rgba(255, 255, 255, 0.08)",
        },
      },
      boxShadow: {
        "glow-hive": "0 0 25px -3px rgba(245, 166, 35, 0.25)",
        "glow-emerald": "0 0 25px -3px rgba(52, 211, 153, 0.25)",
        "glow-cyan": "0 0 25px -3px rgba(0, 212, 255, 0.25)",
        "glass": "0 8px 32px 0 rgba(0, 0, 0, 0.45)",
      },
      fontFamily: {
        sans: ["DM Sans", "system-ui", "sans-serif"],
        mono: ["DM Mono", "monospace"],
        display: ["Space Grotesk", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
