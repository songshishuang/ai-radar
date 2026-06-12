import Link from "next/link";
import { REPORT_TYPE_LABELS } from "@/lib/constants";
import type { ReportSummary } from "@/lib/types";

/** 报告列表：深色玻璃卡，行 hover 高亮，日期等宽数字 */
export default function ReportList({ reports }: { reports: ReportSummary[] }) {
  return (
    <ul className="glass-card divide-y divide-white/[0.06] overflow-hidden">
      {reports.map((r) => (
        <li key={`${r.type}-${r.period_date}-${r.id}`}>
          <Link
            href={`/reports/${r.type}/${r.period_date}`}
            className="group flex flex-wrap items-baseline gap-x-3 gap-y-1 px-4 py-3 transition-colors hover:bg-white/[0.04]"
          >
            <span className="shrink-0 text-sm tabular-nums text-zinc-500">
              {r.period_date}
            </span>
            <span className="text-sm font-medium text-zinc-300 transition-colors group-hover:text-zinc-50">
              {r.title}
            </span>
            <span className="ml-auto shrink-0 text-xs text-zinc-600">
              {REPORT_TYPE_LABELS[r.type] ?? r.type}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
