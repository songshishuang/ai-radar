import type { Metadata } from "next";
import Link from "next/link";
import EmptyState from "@/components/EmptyState";
import ItemCard from "@/components/ItemCard";
import { getJSON } from "@/lib/api";
import { CATEGORY_LABELS } from "@/lib/constants";
import { firstParam } from "@/lib/format";
import type { FeedItem } from "@/lib/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "信息流",
};

type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>;

const CATEGORY_TABS: { key: string; label: string }[] = [
  { key: "", label: "全部" },
  ...Object.entries(CATEGORY_LABELS).map(([key, label]) => ({ key, label })),
];

const SCORE_TABS: { key: string; label: string }[] = [
  { key: "", label: "全部" },
  { key: "6", label: "≥6 关注" },
  { key: "8", label: "≥8 必读" },
];

/** 构造 /feed 链接，保留其余过滤条件 */
function buildFeedHref(category: string, q?: string, minScore?: string) {
  const p = new URLSearchParams();
  if (category) p.set("category", category);
  if (q) p.set("q", q);
  if (minScore) p.set("min_score", minScore);
  const qs = p.toString();
  return qs ? `/feed?${qs}` : "/feed";
}

export default async function FeedPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const sp = await searchParams;
  const rawCategory = firstParam(sp.category) ?? "";
  const category = CATEGORY_LABELS[rawCategory] ? rawCategory : "";
  const q = firstParam(sp.q);
  const rawMinScore = firstParam(sp.min_score) ?? "";
  const minScore = SCORE_TABS.some((t) => t.key === rawMinScore && t.key)
    ? rawMinScore
    : "";

  let items: FeedItem[] = [];
  let failed = false;
  try {
    const apiParams = new URLSearchParams();
    if (category) apiParams.set("category", category);
    if (q) apiParams.set("q", q);
    if (minScore) apiParams.set("min_score", minScore);
    apiParams.set("limit", "50");
    items = await getJSON<FeedItem[]>(`/api/items?${apiParams.toString()}`);
  } catch {
    failed = true;
  }

  return (
    <div>
      <h1 className="text-gradient mb-6 inline-block text-2xl font-bold tracking-tight">
        信息流
      </h1>

      {/* 分类 chip 横向滚动条：激活态渐变填充 */}
      <div className="no-scrollbar -mx-4 mb-4 flex gap-2 overflow-x-auto px-4 pb-1">
        {CATEGORY_TABS.map((tab) => {
          const active = tab.key === category;
          return (
            <Link
              key={tab.key || "all"}
              href={buildFeedHref(tab.key, q, minScore)}
              className={`shrink-0 rounded-full px-3.5 py-1.5 text-sm font-medium transition ${
                active
                  ? "bg-accent-gradient text-white shadow-[0_0_14px_rgba(99,102,241,0.35)]"
                  : "border border-white/10 text-zinc-400 hover:border-white/25 hover:text-zinc-200"
              }`}
            >
              {tab.label}
            </Link>
          );
        })}
      </div>

      {/* min_score 快捷筛选 */}
      <div className="mb-6 flex flex-wrap items-center gap-2 text-xs">
        <span className="text-zinc-600">重要度</span>
        <div className="flex overflow-hidden rounded-lg border border-white/10">
          {SCORE_TABS.map((tab) => {
            const active = tab.key === minScore;
            return (
              <Link
                key={tab.key || "all"}
                href={buildFeedHref(category, q, tab.key)}
                className={`px-3 py-1.5 font-medium tabular-nums transition-colors ${
                  active
                    ? "bg-white/[0.08] text-zinc-50"
                    : "text-zinc-500 hover:bg-white/[0.04] hover:text-zinc-300"
                }`}
              >
                {tab.label}
              </Link>
            );
          })}
        </div>

        {q ? (
          <span className="ml-1 text-zinc-500">
            关键词「<span className="text-zinc-300">{q}</span>」
            <Link
              href={buildFeedHref(category, undefined, minScore)}
              className="ml-1.5 text-cyan-400/80 transition-colors hover:text-cyan-300"
            >
              清除
            </Link>
          </span>
        ) : null}
      </div>

      {items.length > 0 ? (
        <div className="space-y-4">
          {items.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      ) : (
        <EmptyState
          message={failed ? "后端未连接或暂无数据" : "没有符合条件的内容"}
          hint={
            failed
              ? "请确认后端服务已启动（http://localhost:8000），稍后刷新重试。"
              : "试试切换分类或调整过滤条件。"
          }
        />
      )}
    </div>
  );
}
