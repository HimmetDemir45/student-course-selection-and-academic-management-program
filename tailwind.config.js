/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
  ],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "Segoe UI", "Roboto", "Helvetica Neue", "Arial"],
      },
      colors: {
        navy: {
          950: "#050816",
          900: "#0B1220",
          850: "#080A18",
          800: "#0F172A",
          700: "#1E293B",
        },
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(99,102,241,.25), 0 16px 60px rgba(2,6,23,.45)",
        "glow-violet": "0 20px 60px rgba(99,102,241,.35)",
        "glow-cyan": "0 20px 60px rgba(34,211,238,.25)",
      },
    },
  },
  plugins: [],
};
