import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        facturx: {
          primary: "#2563eb",
          "primary-dark": "#1d4ed8",
          "primary-light": "#3b82f6",
          accent: "#0d9488",
          "accent-dark": "#0f766e",
          "accent-light": "#14b8a6",
        },
      },
    },
  },
  plugins: [],
};

export default config;
