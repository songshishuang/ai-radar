import Link from "next/link";
import EmptyState from "@/components/EmptyState";
import { getJSON } from "@/lib/api";
import { REPORT_TYPE_LABELS } from "@/lib/constants";
import { formatDateTime } from "@/lib/format";
import type { ReportDetail } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function ReportDetailPage({
  params,
}: {
  params: Promise<{ type: string; date: string }>;
}) {
  const { type: rawType, date: rawDate } = await params;
  const type = decodeURIComponent(rawType);
  const date = decodeURIComponent(rawDate);
  const typeLabel = REPORT_TYPE_LABELS[type] ?? "报告";

  let report: ReportDetail | null = null;
  try {
    report = await getJSON<ReportDetail>(
      `/api/reports/${encodeURIComponent(type)}/${encodeURIComponent(date)}`
    );
  } catch {
    // 渲染空态
  }

  return (
    <div>
      <nav className="mb-4 text-sm text-gray-500" aria-label="面包屑">
        <Link href="/" className="hover:text-blue-600">
          首页
        </Link>
        <span className="mx-1.5 text-gray-300">/</span>
        <Link
          href={`/reports?type=${encodeURIComponent(type)}`}
          className="hover:text-blue-600"
        >
          {typeLabel}归档
        </Link>
        <span className="mx-1.5 text-gray-300">/</span>
        <span className="text-gray-700">{date}</span>
      </nav>

      {report ? (
        <>
          <header className="mb-6 border-b border-gray-200 pb-4">
            <h1 className="text-2xl font-bold tracking-tight">
              {report.title}
            </h1>
            <p className="mt-2 text-xs text-gray-400">
              {typeLabel} · {report.period_date} · 生成于{" "}
              {formatDateTime(report.created_at)}
            </p>
          </header>
          <article
            className="prose prose-slate max-w-none"
            dangerouslySetInnerHTML={{ __html: report.html }}
          />
        </>
      ) : (
        <EmptyState
          message="未找到该报告，或后端未连接"
          hint="请确认报告日期正确、后端服务已启动（http://localhost:8000）。"
        />
      )}
    </div>
  );
}
