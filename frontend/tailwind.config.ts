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
          raised: "#161d28",
          overlay: "#1b222d",
        },
        border: {
          DEFAULT: "#222d39",
          subtle: "#1a2230",
          strong: "#2e3b4a",
        },
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
