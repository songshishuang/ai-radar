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

/** 切换分类时保留 q / min_score 过滤条件 */
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
  const minScore = firstParam(sp.min_score);

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
      <h1 className="mb-6 text-2xl font-bold tracking-tight">信息流</h1>

      <div className="mb-6 flex flex-wrap gap-1 border-b border-gray-200">
        {CATEGORY_TABS.map((tab) => (
          <Link
            key={tab.key || "all"}
            href={buildFeedHref(tab.key, q, minScore)}
            className={`-mb-px border-b-2 px-3 py-2 text-sm font-medium ${
              tab.key === category
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </Link>
        ))}
      </div>

      {(q || minScore) && (
        <p className="mb-4 text-sm text-gray-500">
          当前过滤：
          {q ? <span className="mr-2">关键词「{q}」</span> : null}
          {minScore ? (
            <span className="mr-2">重要度 ≥ {minScore}</span>
          ) : null}
          <Link
            href={buildFeedHref(category)}
            className="text-blue-600 hover:underline"
          >
            清除
          </Link>
        </p>
      )}

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
