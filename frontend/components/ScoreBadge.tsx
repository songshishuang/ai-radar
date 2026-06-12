/**
 * 重要度徽章（N/10）：
 * - ≥8：红/橙渐变填充 + 脉冲点「必读」
 * - 6-7：紫蓝渐变描边「关注」
 * - ≤5：zinc 暗淡
 */
export default function ScoreBadge({ score }: { score: number }) {
  const s = Number.isFinite(score) ? Math.round(score) : 0;

  if (s >= 8) {
    return (
      <span
        title="重要度"
        className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-gradient-to-r from-red-500 to-orange-500 px-2.5 py-0.5 text-xs font-semibold tabular-nums text-white shadow-[0_0_12px_rgba(249,115,22,0.35)]"
      >
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white" />
        必读 {s}/10
      </span>
    );
  }

  if (s >= 6) {
    return (
      <span
        title="重要度"
        className="inline-flex shrink-0 rounded-full bg-gradient-to-r from-violet-500 to-blue-500 p-px"
      >
        <span className="inline-flex items-center rounded-full bg-[#13131c] px-2.5 py-0.5 text-xs font-semibold tabular-nums text-violet-300">
          关注 {s}/10
        </span>
      </span>
    );
  }

  return (
    <span
      title="重要度"
      className="inline-flex shrink-0 items-center rounded-full border border-zinc-700/60 bg-zinc-800/60 px-2.5 py-0.5 text-xs font-medium tabular-nums text-zinc-500"
    >
      {s}/10
    </span>
  );
}
