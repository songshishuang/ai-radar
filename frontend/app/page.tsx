import Link from "next/link";
import CategoryStats from "@/components/CategoryStats";
import EmptyState from "@/components/EmptyState";
import HeadlineCard from "@/components/HeadlineCard";
import ReportList from "@/components/ReportList";
import { markdownExcerpt, parseHeadlines, parseReportStats } from "@/lib/api";
import { getLatestReport, getReports } from "@/lib/content";
import { formatDateTime } from "@/lib/format";

const WEEKDAYS = ["日", "一", "二", "三", "四", "五", "六"];

function todayLabel(): string {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d} 星期${WEEKDAYS[now.getDay()]}`;
}

export default function HomePage() {
  const latestReport = getLatestReport("daily");
  const recentReports = getReports("daily").slice(0, 7);

  const stats = latestReport ? parseReportStats(latestReport.stats) : null;
  const headlines = latestReport
    ? parseHeadlines(latestReport.headline_analysis)
    : [];
  const tldr =
    stats?.tldr ??
    (latestReport?.markdown ? markdownExcerpt(latestReport.markdown) : "");

  return (
    <div className="space-y-10">
      {/* Hero：渐变大标题 + 当日日期 */}
      <section className="pt-4 text-center">
        <h1 className="text-gradient text-4xl font-bold tracking-tight sm:text-5xl">
          AI 情报站
        </h1>
        <p className="mt-3 text-sm tabular-nums text-zinc-500">
          {todayLabel()}
          {latestReport ? (
            <>
              <span className="mx-2 text-zinc-700">·</span>
              最新日报 {latestReport.period_date}
            </>
          ) : null}
        </p>
      </section>

      {latestReport ? (
        <div className="grid gap-8 lg:grid-cols-3">
          {/* 左侧主栏：今日速览 + 今日必读 */}
          <div className="space-y-8 lg:col-span-2">
            {tldr ? (
              <section className="glass-card accent-left p-5">
                <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold text-zinc-50">
                  <span aria-hidden>⚡</span> 今日速览
                </h2>
                <p className="text-sm leading-relaxed text-zinc-300">{tldr}</p>
                <p className="mt-3 text-xs text-zinc-600">
                  {stats?.total ? `共收录 ${stats.total} 条情报 · ` : ""}
                  生成于 {formatDateTime(latestReport.created_at)} ·{" "}
                  <Link
                    href={`/reports/daily/${latestReport.period_date}`}
                    className="text-cyan-400/80 transition-colors hover:text-cyan-300"
                  >
                    查看完整日报 →
                  </Link>
                </p>
              </section>
            ) : null}

            {headlines.length > 0 ? (
              <section>
                <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-zinc-50">
                  <span aria-hidden>🔥</span> 今日必读
                  <span className="rounded-full bg-white/[0.06] px-2 py-0.5 text-xs font-normal tabular-nums text-zinc-500">
                    {headlines.length}
                  </span>
                </h2>
                <div className="space-y-3">
                  {headlines.map((item, i) => (
                    <HeadlineCard key={item.url || i} item={item} />
                  ))}
                </div>
              </section>
            ) : (
              <article
                className="prose prose-invert max-w-none prose-a:text-cyan-400 prose-a:no-underline hover:prose-a:underline"
                dangerouslySetInnerHTML={{ __html: latestReport.html }}
              />
            )}
          </div>

          {/* 右侧副栏：近期报告 + 分类统计 */}
          <aside className="space-y-8">
            <section>
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-zinc-50">
                  近期报告
                </h2>
                <Link
                  href="/reports"
                  className="text-xs text-zinc-500 transition-colors hover:text-cyan-400"
                >
                  查看归档 →
                </Link>
              </div>
              {recentReports.length > 0 ? (
                <ReportList reports={recentReports} />
              ) : (
                <p className="text-sm text-zinc-600">暂无历史报告。</p>
              )}
            </section>

            {stats?.by_category &&
            Object.keys(stats.by_category).length > 0 ? (
              <section className="glass-card p-5">
                <h2 className="mb-4 text-sm font-semibold text-zinc-50">
                  今日分类分布
                </h2>
                <CategoryStats byCategory={stats.by_category} />
              </section>
            ) : null}
          </aside>
        </div>
      ) : (
        <div className="mx-auto max-w-2xl space-y-6">
          <EmptyState
            message="暂无日报数据"
            hint="本地运行管道生成报告并执行发布脚本后，这里会展示最新一期日报。"
          />
          <div className="flex justify-center gap-3 text-sm">
            <Link
              href="/feed"
              className="rounded-lg border border-white/10 px-4 py-2 text-zinc-300 transition-colors hover:border-white/25 hover:text-zinc-50"
            >
              浏览信息流
            </Link>
            <Link
              href="/subscribe"
              className="bg-accent-gradient rounded-lg px-4 py-2 font-medium text-white transition-opacity hover:opacity-90"
            >
              订阅报告
            </Link>
          </div>
          {recentReports.length > 0 ? (
            <section>
              <h2 className="mb-3 text-sm font-semibold text-zinc-50">
                近期报告
              </h2>
              <ReportList reports={recentReports} />
            </section>
          ) : null}
        </div>
      )}
    </div>
  );
}
