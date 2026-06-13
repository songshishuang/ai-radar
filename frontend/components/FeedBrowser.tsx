"use client";

import { useMemo, useState } from "react";
import EmptyState from "@/components/EmptyState";
import ItemCard from "@/components/ItemCard";
import { CATEGORY_LABELS } from "@/lib/constants";
import type { FeedItem } from "@/lib/types";

const CATEGORY_TABS = [
  { key: "", label: "全部" },
  ...Object.entries(CATEGORY_LABELS).map(([key, label]) => ({ key, label })),
];

const SCORE_TABS = [
  { key: 0, label: "全部" },
  { key: 6, label: "≥6 关注" },
  { key: 8, label: "≥8 必读" },
];

/** 信息流：客户端分类 / 重要度 / 关键词筛选（全部条目构建期注入）。 */
export default function FeedBrowser({
  items,
  initialQuery = "",
}: {
  items: FeedItem[];
  initialQuery?: string;
}) {
  const [category, setCategory] = useState("");
  const [minScore, setMinScore] = useState(0);
  const [q, setQ] = useState(initialQuery);

  const filtered = useMemo(() => {
    const kw = q.trim().toLowerCase();
    return items.filter((it) => {
      if (category && it.category !== category) return false;
      if (minScore && it.importance_score < minScore) return false;
      if (kw) {
        const hay = `${it.title} ${it.summary_zh} ${(it.entities ?? []).join(
          " "
        )} ${(it.tags ?? []).join(" ")}`.toLowerCase();
        if (!hay.includes(kw)) return false;
      }
      return true;
    });
  }, [items, category, minScore, q]);

  return (
    <div>
      <h1 className="text-gradient mb-6 inline-block text-2xl font-bold tracking-tight">
        信息流
      </h1>

      {/* 分类 chip 横向滚动条 */}
      <div className="no-scrollbar -mx-4 mb-4 flex gap-2 overflow-x-auto px-4 pb-1">
        {CATEGORY_TABS.map((tab) => {
          const active = tab.key === category;
          return (
            <button
              key={tab.key || "all"}
              type="button"
              onClick={() => setCategory(tab.key)}
              className={`shrink-0 rounded-full px-3.5 py-1.5 text-sm font-medium transition ${
                active
                  ? "bg-accent-gradient text-white shadow-[0_0_14px_rgba(99,102,241,0.35)]"
                  : "border border-white/10 text-zinc-400 hover:border-white/25 hover:text-zinc-200"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* 重要度 + 搜索 */}
      <div className="mb-6 flex flex-wrap items-center gap-3 text-xs">
        <div className="flex items-center gap-2">
          <span className="text-zinc-600">重要度</span>
          <div className="flex overflow-hidden rounded-lg border border-white/10">
            {SCORE_TABS.map((tab) => {
              const active = tab.key === minScore;
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setMinScore(tab.key)}
                  className={`px-3 py-1.5 font-medium tabular-nums transition-colors ${
                    active
                      ? "bg-white/[0.08] text-zinc-50"
                      : "text-zinc-500 hover:bg-white/[0.04] hover:text-zinc-300"
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="筛选关键词…"
          className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-sm text-zinc-200 outline-none transition focus:border-white/30 placeholder:text-zinc-600"
        />
        <span className="text-zinc-600 tabular-nums">{filtered.length} 条</span>
      </div>

      {filtered.length > 0 ? (
        <div className="space-y-4">
          {filtered.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      ) : (
        <EmptyState
          message="没有符合条件的内容"
          hint="试试切换分类或调整筛选条件。"
        />
      )}
    </div>
  );
}
