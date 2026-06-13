"use client";

import { useState } from "react";
import EmptyState from "@/components/EmptyState";
import ReportList from "@/components/ReportList";
import { REPORT_TYPES, REPORT_TYPE_LABELS } from "@/lib/constants";
import type { ReportSummary, ReportType } from "@/lib/types";

/** 报告归档：客户端类型 tab 切换（静态导出无后端，全部报告构建期注入）。 */
export default function ReportsBrowser({
  reports,
}: {
  reports: ReportSummary[];
}) {
  const [type, setType] = useState<ReportType>("daily");
  const filtered = reports.filter((r) => r.type === type);

  return (
    <div>
      <h1 className="text-gradient mb-6 inline-block text-2xl font-bold tracking-tight">
        报告归档
      </h1>

      <div className="mb-6 flex gap-6 border-b border-white/[0.06] pb-px">
        {REPORT_TYPES.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setType(t)}
            className={`gradient-underline pb-2 text-sm font-medium transition-colors ${
              t === type
                ? "is-active text-zinc-50"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {REPORT_TYPE_LABELS[t]}
          </button>
        ))}
      </div>

      {filtered.length > 0 ? (
        <ReportList reports={filtered} />
      ) : (
        <EmptyState message={`暂无${REPORT_TYPE_LABELS[type]}数据`} />
      )}
    </div>
  );
}
