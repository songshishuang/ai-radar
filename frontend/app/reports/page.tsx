import type { Metadata } from "next";
import Link from "next/link";
import EmptyState from "@/components/EmptyState";
import ReportList from "@/components/ReportList";
import { getJSON } from "@/lib/api";
import { REPORT_TYPES, REPORT_TYPE_LABELS } from "@/lib/constants";
import { firstParam } from "@/lib/format";
import type { ReportSummary, ReportType } from "@/lib/types";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "报告归档",
};

type SearchParams = Promise<{ [key: string]: string | string[] | undefined }>;

export default async function ReportsPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const sp = await searchParams;
  const rawType = firstParam(sp.type) ?? "daily";
  const type: ReportType = (REPORT_TYPES as readonly string[]).includes(rawType)
    ? (rawType as ReportType)
    : "daily";

  let reports: ReportSummary[] = [];
  let failed = false;
  try {
    reports = await getJSON<ReportSummary[]>(
      `/api/reports?type=${type}&limit=20`
    );
  } catch {
    failed = true;
  }

  return (
    <div>
      <h1 className="text-gradient mb-6 inline-block text-2xl font-bold tracking-tight">
        报告归档
      </h1>

      {/* type tab：渐变下划线激活态 */}
      <div className="mb-6 flex gap-6 border-b border-white/[0.06] pb-px">
        {REPORT_TYPES.map((t) => (
          <Link
            key={t}
            href={`/reports?type=${t}`}
            className={`gradient-underline pb-2 text-sm font-medium transition-colors ${
              t === type
                ? "is-active text-zinc-50"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {REPORT_TYPE_LABELS[t]}
          </Link>
        ))}
      </div>

      {reports.length > 0 ? (
        <ReportList reports={reports} />
      ) : (
        <EmptyState
          message={
            failed
              ? "后端未连接或暂无数据"
              : `暂无${REPORT_TYPE_LABELS[type]}数据`
          }
        />
      )}
    </div>
  );
}
