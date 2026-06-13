"use client";

import { useMemo, useState } from "react";
import EmptyState from "@/components/EmptyState";
import ItemCard from "@/components/ItemCard";
import type { FeedItem } from "@/lib/types";

/** 搜索：客户端全量条目关键词检索（标题 / 摘要 / 公司产品名 / 标签）。 */
export default function SearchBrowser({ items }: { items: FeedItem[] }) {
  const [q, setQ] = useState("");
  const kw = q.trim().toLowerCase();

  const results = useMemo(() => {
    if (!kw) return [];
    return items.filter((it) => {
      const hay = `${it.title} ${it.summary_zh} ${(it.entities ?? []).join(
        " "
      )} ${(it.tags ?? []).join(" ")}`.toLowerCase();
      return hay.includes(kw);
    });
  }, [items, kw]);

  return (
    <div>
      <h1 className="text-gradient mb-6 inline-block text-2xl font-bold tracking-tight">
        搜索
      </h1>

      <div className="mb-8 flex gap-2">
        <div className="w-full rounded-xl bg-white/10 p-px transition focus-within:bg-accent focus-within:shadow-[0_0_18px_var(--accent-glow)]">
          <input
            type="search"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            autoFocus
            placeholder="搜索标题、摘要、公司 / 产品名…"
            className="w-full rounded-[11px] bg-[#101016] px-4 py-2.5 text-sm text-zinc-200 outline-none placeholder:text-zinc-600"
          />
        </div>
      </div>

      {kw ? (
        results.length > 0 ? (
          <>
            <p className="mb-4 text-sm text-zinc-500">
              「<span className="text-zinc-300">{q}</span>」共{" "}
              <span className="tabular-nums text-zinc-300">
                {results.length}
              </span>{" "}
              条结果
            </p>
            <div className="space-y-4">
              {results.map((item) => (
                <ItemCard key={item.id} item={item} />
              ))}
            </div>
          </>
        ) : (
          <EmptyState
            message={`未找到与「${q}」相关的内容`}
            hint="换个关键词试试。"
          />
        )
      ) : (
        <p className="text-center text-sm text-zinc-600">
          输入关键词，搜索全部情报条目。
        </p>
      )}
    </div>
  );
}
