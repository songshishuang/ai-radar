import type { Metadata } from "next";
import Link from "next/link";
const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "AI 情报站",
    template: "%s · AI 情报站",
  },
  description: "AI 行业情报聚合：日报 / 周报 / 月报与实时信息流",
};

const NAV_LINKS = [
  { href: "/", label: "首页" },
  { href: "/reports", label: "报告归档" },
  { href: "/feed", label: "信息流" },
  { href: "/search", label: "搜索" },
  { href: "/subscribe", label: "订阅" },
];

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        {/* 运行时加载等宽字体（无构建期网络依赖），离线则回落系统 mono */}
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap"
        />
      </head>
      <body className="relative flex min-h-screen flex-col overflow-x-hidden bg-void font-sans text-zinc-300">
        {/* 全局底纹：极淡网格 + 边缘淡出（纯 CSS，零依赖） */}
        <div
          aria-hidden
          className="bg-grid mask-edge pointer-events-none fixed inset-0 -z-20 opacity-[0.4]"
        />
        {/* 单一 accent 顶部辉光（收敛自三色光斑） */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[420px] overflow-hidden"
        >
          <div className="absolute -top-28 left-1/2 h-72 w-[36rem] -translate-x-1/2 rounded-full bg-accent opacity-[0.12] blur-3xl" />
        </div>

        <header className="sticky top-0 z-20 border-b border-edge bg-void/70 backdrop-blur-xl">
          <nav className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
            <Link href="/" className="flex items-center gap-2">
              <span
                aria-hidden
                className="grid h-5 w-5 place-items-center rounded-md border border-accent/40 bg-accent/10 text-[10px] font-bold text-accent shadow-[0_0_14px_var(--accent-glow)]"
              >
                ◢
              </span>
              <span className="font-mono text-base font-semibold tracking-tight text-zinc-50">
                ai<span className="text-accent">·</span>radar
              </span>
            </Link>
            <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-sm text-zinc-400">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="gradient-underline py-1 transition-colors hover:text-zinc-50"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </nav>
        </header>

        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8">
          {children}
        </main>

        <footer className="border-t border-white/[0.06]">
          <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-4 gap-y-1 px-4 py-5 text-sm text-zinc-500">
            <span className="flex items-center gap-2">
              <span
                aria-hidden
                className="h-3 w-3 rounded-sm bg-accent opacity-70"
              />
              AI Intel
            </span>
            <a
              href={`${BASE_PATH}/rss/daily.xml`}
              className="transition-colors hover:text-accent"
            >
              RSS 订阅 /rss/daily.xml
            </a>
          </div>
        </footer>
      </body>
    </html>
  );
}
