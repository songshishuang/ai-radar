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
      <h1 className="mb-6 text-2xl font-bold tracking-tight">报告归档</h1>

      <div className="mb-6 flex gap-1 border-b border-gray-200">
        {REPORT_TYPES.map((t) => (
          <Link
            key={t}
            href={`/reports?type=${t}`}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium ${
              t === type
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
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
