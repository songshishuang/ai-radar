import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";

/**
 * 设计语言 v2（据 AI 资讯站标杆调研重做）：
 * - 收敛渐变：全站铺的三色渐变 → 单一 accent「像标点一样」稀疏用；色板基于 OKLCH（感知均匀）。
 * - 中性为主：surface/border 走近中性冷灰，accent 只承载语义（必读/激活/链接）。
 * - 等宽数字：font-mono（JetBrains Mono）用于分数/计数/时间，营造技术感。
 * 具体色值见 globals.css 的 :root（OKLCH 定义）。
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx,mdx}", "./components/**/*.{ts,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        // 分量 var + <alpha-value> 占位 → 支持 bg-panel/80、border-accent/40 等透明度修饰
        void: "oklch(var(--bg) / <alpha-value>)",
        panel: "oklch(var(--surface-1) / <alpha-value>)",
        "panel-2": "oklch(var(--surface-2) / <alpha-value>)",
        accent: "oklch(var(--accent) / <alpha-value>)",
        "accent-strong": "oklch(var(--accent-strong) / <alpha-value>)",
        // 完整色（不接受透明度修饰，直接用）
        edge: "var(--border)",
        "edge-strong": "var(--border-strong)",
        "accent-soft": "var(--accent-soft)",
      },
      fontFamily: {
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      backgroundImage: {
        // 仅保留给 wordmark / 英雄区的克制双停渐变（靛→青），其余一律单色 accent
        "accent-sheen": "var(--grad-hero)",
      },
      boxShadow: {
        glow: "0 0 0 1px var(--border) , 0 0 24px -8px var(--accent-glow)",
      },
      animation: {
        "fade-up": "fade-up 0.45s ease both",
        "pulse-dot": "pulse-dot 1.8s ease-in-out infinite",
        scan: "scan 6s linear infinite",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.4", transform: "scale(0.8)" },
        },
        scan: {
          from: { transform: "translateY(-100%)" },
          to: { transform: "translateY(100%)" },
        },
      },
    },
  },
  plugins: [typography],
};

export default config;
