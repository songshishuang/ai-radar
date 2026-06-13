"use client";

import { useState } from "react";

const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const FEEDS = [
  { key: "daily", label: "日报", desc: "每天一期，速览过去 24 小时" },
  { key: "weekly", label: "周报", desc: "每周一期，提炼一周趋势" },
  { key: "monthly", label: "月报", desc: "每月一期，纵览行业大局" },
  { key: "feed", label: "全量条目", desc: "所有情报条目实时流" },
];

export default function SubscribePage() {
  const [copied, setCopied] = useState<string>("");

  function rssUrl(key: string): string {
    const origin =
      typeof window !== "undefined" ? window.location.origin : "";
    return `${origin}${BASE_PATH}/rss/${key}.xml`;
  }

  async function copy(key: string) {
    try {
      await navigator.clipboard.writeText(rssUrl(key));
      setCopied(key);
      setTimeout(() => setCopied(""), 1600);
    } catch {
      setCopied("");
    }
  }

  return (
    <div className="mx-auto max-w-lg pt-6">
      <h1 className="text-gradient mb-2 inline-block text-2xl font-bold tracking-tight">
        订阅
      </h1>
      <p className="mb-8 text-sm text-zinc-500">
        用任意 RSS 阅读器（Reeder / Folo / Feedly 等）订阅以下任一源，新报告自动推送。
      </p>

      <div className="space-y-3">
        {FEEDS.map((f) => (
          <div
            key={f.key}
            className="glass-card card-hover flex items-center justify-between gap-4 p-4"
          >
            <div>
              <p className="text-sm font-medium text-zinc-100">{f.label}</p>
              <p className="text-xs text-zinc-500">{f.desc}</p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <a
                href={`${BASE_PATH}/rss/${f.key}.xml`}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-zinc-300 transition hover:border-white/25 hover:text-zinc-50"
              >
                打开
              </a>
              <button
                type="button"
                onClick={() => copy(f.key)}
                className="bg-accent-gradient rounded-lg px-3 py-1.5 text-xs font-medium text-white transition hover:opacity-90"
              >
                {copied === f.key ? "已复制 ✓" : "复制链接"}
              </button>
            </div>
          </div>
        ))}
      </div>

      <p className="mt-8 text-xs leading-relaxed text-zinc-600">
        想要邮件 / 企业微信 / Telegram 推送？这些由自托管的完整版（FastAPI 后端）提供，
        见仓库 <code className="text-zinc-400">deploy/</code> 说明。当前为 GitHub Pages
        静态站，提供网页浏览与 RSS 订阅。
      </p>
    </div>
  );
}
