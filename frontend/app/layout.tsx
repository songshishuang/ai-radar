import type { Metadata } from "next";
import Link from "next/link";
import { API_BASE } from "@/lib/api";
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
    <html lang="zh-CN">
      <body className="flex min-h-screen flex-col bg-gray-50 font-sans text-gray-900">
        <header className="sticky top-0 z-10 border-b border-gray-200 bg-white/90 backdrop-blur">
          <nav className="mx-auto flex max-w-4xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
            <Link href="/" className="text-lg font-bold tracking-tight">
              AI 情报站
            </Link>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-gray-600">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="hover:text-blue-600"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </nav>
        </header>

        <main className="mx-auto w-full max-w-4xl flex-1 px-4 py-8">
          {children}
        </main>

        <footer className="border-t border-gray-200 bg-white">
          <div className="mx-auto max-w-4xl px-4 py-4 text-sm text-gray-500">
            AI Intel · RSS:{" "}
            <a
              href={`${API_BASE}/rss/daily.xml`}
              className="hover:text-blue-600 hover:underline"
            >
              /rss/daily.xml
            </a>
          </div>
        </footer>
      </body>
    </html>
  );
}
