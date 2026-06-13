import Link from "next/link";
import EmptyState from "@/components/EmptyState";
import { REPORT_TYPE_LABELS } from "@/lib/constants";
import { getReport, getReports } from "@/lib/content";
import { formatDateTime } from "@/lib/format";

/** 静态导出：枚举全部报告，为每份生成一个静态页面 */
export function generateStaticParams() {
  return getReports().map((r) => ({ type: r.type, date: r.period_date }));
}

export default async function ReportDetailPage({
  params,
}: {
  params: Promise<{ type: string; date: string }>;
}) {
  const { type: rawType, date: rawDate } = await params;
  const type = decodeURIComponent(rawType);
  const date = decodeURIComponent(rawDate);
  const typeLabel = REPORT_TYPE_LABELS[type] ?? "报告";

  const report = getReport(type, date);

  return (
    <div>
      <nav className="mb-5 text-sm text-zinc-500" aria-label="面包屑">
        <Link href="/" className="transition-colors hover:text-accent">
          首页
        </Link>
        <span className="mx-1.5 text-zinc-700">/</span>
        <Link
          href={`/reports?type=${encodeURIComponent(type)}`}
          className="transition-colors hover:text-accent"
        >
          {typeLabel}归档
        </Link>
        <span className="mx-1.5 text-zinc-700">/</span>
        <span className="tabular-nums text-zinc-300">{date}</span>
      </nav>

      {report ? (
        <>
          <header className="mb-8 border-b border-white/[0.06] pb-6">
            <h1 className="text-gradient inline-block text-3xl font-bold tracking-tight">
              {report.title}
            </h1>
            <p className="mt-3 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
              <span className="rounded-full border border-white/10 px-2 py-0.5">
                {typeLabel}
              </span>
              <span className="tabular-nums">{report.period_date}</span>
              <span className="text-zinc-700">·</span>
              <span className="tabular-nums">
                生成于 {formatDateTime(report.created_at)}
              </span>
            </p>
          </header>
          <article
            className="prose prose-invert max-w-none prose-headings:tracking-tight prose-a:text-accent prose-a:no-underline hover:prose-a:underline prose-blockquote:border-l-accent/50 prose-blockquote:text-zinc-400 prose-strong:text-zinc-100 prose-hr:border-white/[0.08]"
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
