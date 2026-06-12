import Link from "next/link";
import EmptyState from "@/components/EmptyState";
import ReportList from "@/components/ReportList";
import { getJSON } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { ReportDetail, ReportSummary } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let latestReport: ReportDetail | null = null;
  let recentReports: ReportSummary[] = [];

  try {
    const latest = await getJSON<ReportSummary[]>(
      "/api/reports?type=daily&limit=1"
    );
    if (latest.length > 0) {
      latestReport = await getJSON<ReportDetail>(
        `/api/reports/daily/${encodeURIComponent(latest[0].period_date)}`
      );
    }
  } catch {
    // 后端未连接或暂无数据，渲染空态
  }

  try {
    recentReports = await getJSON<ReportSummary[]>(
      "/api/reports?type=daily&limit=7"
    );
  } catch {
    // 忽略，列表区展示空提示
  }

  return (
    <div className="space-y-10">
      {latestReport ? (
        <section>
          <div className="mb-6 border-b border-gray-200 pb-4">
            <p className="text-sm text-gray-500">
              最新日报 · {latestReport.period_date}
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight">
              {latestReport.title}
            </h1>
            <p className="mt-1 text-xs text-gray-400">
              生成于 {formatDateTime(latestReport.created_at)}
            </p>
          </div>
          <article
            className="prose prose-slate max-w-none"
            dangerouslySetInnerHTML={{ __html: latestReport.html }}
          />
        </section>
      ) : (
        <section>
          <h1 className="mb-4 text-2xl font-bold tracking-tight">
            AI 情报站
          </h1>
          <EmptyState
            message="后端未连接或暂无数据"
            hint="暂时没有可展示的日报。启动后端服务（http://localhost:8000）并生成报告后，这里会自动展示最新日报。"
          />
          <div className="mt-4 flex justify-center gap-3 text-sm">
            <Link
              href="/feed"
              className="rounded-md border border-gray-300 bg-white px-4 py-2 text-gray-700 hover:bg-gray-50"
            >
              浏览信息流
            </Link>
            <Link
              href="/subscribe"
              className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              订阅报告
            </Link>
          </div>
        </section>
      )}

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">最近报告</h2>
          <Link
            href="/reports"
            className="text-sm text-blue-600 hover:underline"
          >
            查看归档 →
          </Link>
        </div>
        {recentReports.length > 0 ? (
          <ReportList reports={recentReports} />
        ) : (
          <p className="text-sm text-gray-400">暂无历史报告。</p>
        )}
      </section>
    </div>
  );
}
