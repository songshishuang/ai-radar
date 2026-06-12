import type { Metadata } from "next";
import EmptyState from "@/components/EmptyState";
import ItemCard from "@/components/ItemCard";
import { getJSON } from "@/lib/api";
import { firstParam } from "@/lib/format";
import type { FeedItem } from "@/lib/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "搜索",
};

type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>;

export default async function SearchPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const sp = await searchParams;
  const q = (firstParam(sp.q) ?? "").trim();

  let items: FeedItem[] = [];
  let failed = false;
  if (q) {
    try {
      items = await getJSON<FeedItem[]>(
        `/api/items?q=${encodeURIComponent(q)}&limit=50`
      );
    } catch {
      failed = true;
    }
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold tracking-tight">搜索</h1>

      <form action="/search" method="get" className="mb-8 flex gap-2">
        <input
          type="search"
          name="q"
          defaultValue={q}
          placeholder="搜索标题、摘要关键词…"
          className="w-full rounded-md border border-gray-300 bg-white px-4 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
        <button
          type="submit"
          className="shrink-0 rounded-md bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          搜索
        </button>
      </form>

      {q ? (
        items.length > 0 ? (
          <>
            <p className="mb-4 text-sm text-gray-500">
              「{q}」共 {items.length} 条结果
            </p>
            <div className="space-y-4">
              {items.map((item) => (
                <ItemCard key={item.id} item={item} />
              ))}
            </div>
          </>
        ) : (
          <EmptyState
            message={
              failed ? "后端未连接或暂无数据" : `未找到与「${q}」相关的内容`
            }
            hint={
              failed
                ? "请确认后端服务已启动（http://localhost:8000），稍后刷新重试。"
                : "换个关键词试试。"
            }
          />
        )
      ) : (
        <p className="text-center text-sm text-gray-400">
          输入关键词，搜索全部情报条目。
        </p>
      )}
    </div>
  );
}
