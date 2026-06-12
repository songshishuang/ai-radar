import Link from "next/link";
import ScoreBadge from "@/components/ScoreBadge";
import { categoryLabel } from "@/lib/constants";
import { formatDateTime } from "@/lib/format";
import type { FeedItem } from "@/lib/types";

/** 信息流条目卡：玻璃拟态 + hover 上浮；高分条目带左侧渐变竖条 */
export default function ItemCard({ item }: { item: FeedItem }) {
  const tags = Array.isArray(item.tags) ? item.tags : [];
  const entities = Array.isArray(item.entities) ? item.entities : [];
  const label = categoryLabel(item.category);
  const important = item.importance_score >= 8;

  return (
    <article
      className={`glass-card card-hover p-4 ${important ? "accent-left pl-5" : ""}`}
    >
      <div className="flex items-start justify-between gap-3">
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="bg-gradient-to-r from-violet-400 via-blue-400 to-cyan-300 bg-clip-text font-medium leading-snug text-zinc-50 transition-colors hover:text-transparent"
        >
          {item.title}
        </a>
        <ScoreBadge score={item.importance_score} />
      </div>

      {item.summary_zh ? (
        <p className="mt-2 text-sm leading-relaxed text-zinc-400">
          {item.summary_zh}
        </p>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1.5 text-xs">
        {label ? (
          <span className="rounded-md bg-blue-500/10 px-1.5 py-0.5 font-medium text-blue-400">
            {label}
          </span>
        ) : null}
        {entities.map((entity) => (
          <Link
            key={entity}
            href={`/search?q=${encodeURIComponent(entity)}`}
            className="rounded-md border border-violet-400/30 bg-violet-500/10 px-1.5 py-0.5 text-violet-300 transition-colors hover:border-violet-400/60 hover:text-violet-200"
          >
            {entity}
          </Link>
        ))}
        {tags.map((tag) => (
          <span
            key={tag}
            className="rounded-md bg-white/[0.06] px-1.5 py-0.5 text-zinc-500"
          >
            {tag}
          </span>
        ))}
        <span className="ml-auto flex items-center gap-2 text-zinc-600">
          {item.source ? <span>{item.source}</span> : null}
          {item.published_at ? (
            <time dateTime={item.published_at} className="tabular-nums">
              {formatDateTime(item.published_at)}
            </time>
          ) : null}
        </span>
      </div>
    </article>
  );
}
