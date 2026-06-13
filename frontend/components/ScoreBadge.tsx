/**
 * 重要度徽章（N/10），数字走等宽（技术感）。收敛配色：
 * - ≥8：单一暖色 amber 填充 + 脉冲点「必读」——全站唯一保留的语义警示色，在冷调站里自然「发烫」
 * - 6-7：accent（青蓝）描边「关注」
 * - ≤5：zinc 暗淡
 */
export default function ScoreBadge({ score }: { score: number }) {
  const s = Number.isFinite(score) ? Math.round(score) : 0;

  if (s >= 8) {
    return (
      <span
        title="重要度"
        className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-amber-500/90 px-2.5 py-0.5 font-mono text-xs font-semibold tabular text-[#1a1205] shadow-[0_0_12px_rgba(245,158,11,0.4)]"
      >
        <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-[#1a1205]" />
        必读 {s}/10
      </span>
    );
  }

  if (s >= 6) {
    return (
      <span
        title="重要度"
        className="inline-flex shrink-0 items-center rounded-full border border-accent/40 bg-accent-soft px-2.5 py-0.5 font-mono text-xs font-semibold tabular text-accent"
      >
        关注 {s}/10
      </span>
    );
  }

  return (
    <span
      title="重要度"
      className="inline-flex shrink-0 items-center rounded-full border border-edge bg-white/[0.04] px-2.5 py-0.5 font-mono text-xs font-medium tabular text-zinc-500"
    >
      {s}/10
    </span>
  );
}
