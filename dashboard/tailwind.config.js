/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"IBM Plex Sans"', "system-ui", "-apple-system", '"Segoe UI"', "sans-serif"],
      },
      colors: {
        page: "#0e1216",
        surface: "#151a20",
        raised: "#1c2229",
        line: "rgba(255,255,255,0.08)",
        ink: "#eef1f4",
        ink2: "#aab3bd",
        ink3: "#6f7a86",
        soc: { high: "#3ecf6a", mid: "#f2b43a", low: "#e5484d" },
        temp: "#3987e5",
        series: {
          blue: "#3987e5",
          orange: "#d95926",
          aqua: "#199e70",
          yellow: "#c98500",
          violet: "#9085e9",
          magenta: "#d55181",
        },
      },
      borderRadius: { card: "14px" },
    },
  },
  plugins: [],
};
