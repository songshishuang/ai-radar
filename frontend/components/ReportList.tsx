import Link from "next/link";
import type { ReportSummary } from "@/lib/types";

/** 报告链接列表：period_date + title，链到详情页 */
export default function ReportList({ reports }: { reports: ReportSummary[] }) {
  return (
    <ul className="divide-y divide-gray-100 overflow-hidden rounded-lg border border-gray-200 bg-white">
      {reports.map((r) => (
        <li key={`${r.type}-${r.period_date}-${r.id}`}>
          <Link
            href={`/reports/${r.type}/${r.period_date}`}
            className="flex flex-wrap items-baseline gap-x-3 gap-y-1 px-4 py-3 hover:bg-gray-50"
          >
            <span className="shrink-0 text-sm tabular-nums text-gray-500">
              {r.period_date}
            </span>
            <span className="text-sm font-medium text-gray-900">
              {r.title}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
