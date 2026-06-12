import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

const config: Config = {
  content: ["./app/**/*.{ts,tsx,mdx}", "./components/**/*.{ts,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        /** 全站底色：近黑深空 */
        void: "#0a0a0f",
        /** 玻璃卡片底色（配合 backdrop-blur 使用） */
        panel: "rgba(24,24,32,0.7)",
        /** 1px 玻璃边框 */
        edge: "rgba(255,255,255,0.08)",
      },
      backgroundImage: {
        /** 品牌 accent 渐变：violet → blue → cyan */
        accent: "linear-gradient(135deg, #8b5cf6 0%, #3b82f6 50%, #22d3ee 100%)",
      },
      animation: {
        "fade-up": "fade-up 0.45s ease both",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [typography],
};

export default config;
