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
      <body className="relative flex min-h-screen flex-col overflow-x-hidden bg-void font-sans text-zinc-300">
        {/* 背景光晕：顶部 violet / blue 模糊光斑 */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[480px] overflow-hidden"
        >
          <div className="absolute -top-32 left-1/4 h-80 w-80 rounded-full bg-violet-600 opacity-20 blur-3xl" />
          <div className="absolute -top-20 right-1/4 h-72 w-72 rounded-full bg-blue-600 opacity-20 blur-3xl" />
          <div className="absolute top-10 left-1/2 h-56 w-56 -translate-x-1/2 rounded-full bg-cyan-500 opacity-10 blur-3xl" />
        </div>

        <header className="sticky top-0 z-20 border-b border-white/[0.06] bg-void/70 backdrop-blur-xl">
          <nav className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
            <Link href="/" className="flex items-center gap-2">
              <span
                aria-hidden
                className="h-5 w-5 rounded-md bg-gradient-to-br from-violet-500 via-blue-500 to-cyan-400 shadow-[0_0_14px_rgba(99,102,241,0.5)]"
              />
              <span className="text-lg font-bold tracking-tight text-zinc-50">
                AI 情报站
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
                className="h-3 w-3 rounded-sm bg-gradient-to-br from-violet-500 via-blue-500 to-cyan-400 opacity-70"
              />
              AI Intel
            </span>
            <a
              href={`${BASE_PATH}/rss/daily.xml`}
              className="transition-colors hover:text-cyan-400"
            >
              RSS 订阅 /rss/daily.xml
            </a>
          </div>
        </footer>
      </body>
    </html>
  );
}
