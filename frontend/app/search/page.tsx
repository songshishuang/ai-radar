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
      <h1 className="text-gradient mb-6 inline-block text-2xl font-bold tracking-tight">
        搜索
      </h1>

      <form action="/search" method="get" className="mb-8 flex gap-2">
        {/* 渐变描边输入框：wrapper p-px，focus-within 时渐变点亮 */}
        <div className="w-full rounded-xl bg-white/10 p-px transition focus-within:bg-gradient-to-r focus-within:from-violet-500 focus-within:via-blue-500 focus-within:to-cyan-400 focus-within:shadow-[0_0_18px_rgba(99,102,241,0.25)]">
          <input
            type="search"
            name="q"
            defaultValue={q}
            placeholder="搜索标题、摘要、公司 / 产品名…"
            className="w-full rounded-[11px] bg-[#101016] px-4 py-2.5 text-sm text-zinc-200 outline-none placeholder:text-zinc-600"
          />
        </div>
        <button
          type="submit"
          className="bg-accent-gradient shrink-0 rounded-xl px-5 py-2.5 text-sm font-medium text-white transition-opacity hover:opacity-90"
        >
          搜索
        </button>
      </form>

      {q ? (
        items.length > 0 ? (
          <>
            <p className="mb-4 text-sm text-zinc-500">
              「<span className="text-zinc-300">{q}</span>」共{" "}
              <span className="tabular-nums text-zinc-300">
                {items.length}
              </span>{" "}
              条结果
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
        <p className="text-center text-sm text-zinc-600">
          输入关键词，搜索全部情报条目。
        </p>
      )}
    </div>
  );
}
