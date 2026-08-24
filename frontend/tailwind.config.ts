import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        critical: "#DC2626",
        high: "#EA580C",
        medium: "#CA8A04",
        low: "#6B7280",
      },
    },
  },
  plugins: [],
};
export default config;
