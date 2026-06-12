import type { FeedItem } from "@/lib/types";
import { CATEGORY_LABELS } from "@/lib/constants";
import { formatDateTime } from "@/lib/format";

/** 重要度徽章配色：≥8 红、≥6 橙、其余灰 */
function badgeClass(score: number): string {
  if (score >= 8) return "bg-red-100 text-red-700";
  if (score >= 6) return "bg-orange-100 text-orange-700";
  return "bg-gray-100 text-gray-600";
}

export default function ItemCard({ item }: { item: FeedItem }) {
  const tags = Array.isArray(item.tags) ? item.tags : [];
  const categoryLabel = CATEGORY_LABELS[item.category];

  return (
    <article className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium leading-snug text-gray-900 hover:text-blue-600 hover:underline"
        >
          {item.title}
        </a>
        <span
          title="重要度"
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums ${badgeClass(
            item.importance_score
          )}`}
        >
          {item.importance_score}
        </span>
      </div>

      {item.summary_zh ? (
        <p className="mt-2 text-sm leading-relaxed text-gray-600">
          {item.summary_zh}
        </p>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-1.5 text-xs">
        {categoryLabel ? (
          <span className="rounded bg-blue-50 px-1.5 py-0.5 text-blue-600">
            {categoryLabel}
          </span>
        ) : null}
        {tags.map((tag) => (
          <span
            key={tag}
            className="rounded bg-gray-100 px-1.5 py-0.5 text-gray-500"
          >
            {tag}
          </span>
        ))}
        <span className="ml-auto flex items-center gap-2 text-gray-400">
          {item.source ? <span>{item.source}</span> : null}
          {item.published_at ? (
            <time dateTime={item.published_at}>
              {formatDateTime(item.published_at)}
            </time>
          ) : null}
        </span>
      </div>
    </article>
  );
}
