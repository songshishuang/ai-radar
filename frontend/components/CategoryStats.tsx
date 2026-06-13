import { categoryLabel } from "@/lib/constants";

/** stats.by_category → 横向渐变条（按数量降序，宽度按最大值归一化） */
export default function CategoryStats({
  byCategory,
}: {
  byCategory: Record<string, number>;
}) {
  const entries = Object.entries(byCategory)
    .filter(([, n]) => typeof n === "number" && n > 0)
    .sort(([, a], [, b]) => b - a);
  if (entries.length === 0) return null;
  const max = Math.max(...entries.map(([, n]) => n));

  return (
    <div className="space-y-2.5">
      {entries.map(([key, count]) => (
        <div key={key} className="flex items-center gap-2 text-xs">
          <span className="w-16 shrink-0 truncate text-zinc-400">
            {categoryLabel(key)}
          </span>
          <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
            <span
              className="block h-full rounded-full bg-accent-gradient"
              style={{ width: `${Math.max((count / max) * 100, 4)}%` }}
            />
          </span>
          <span className="w-6 shrink-0 text-right font-mono tabular text-zinc-500">
            {count}
          </span>
        </div>
      ))}
    </div>
  );
}
