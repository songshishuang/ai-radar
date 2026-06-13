"use client";

import { useState } from "react";
import type { ReportDetail } from "@/lib/types";

const LENS_LABELS: Record<string, string> = {
  pm: "产品视角",
  engineer: "研发视角",
  investor: "投资视角",
  researcher: "研究视角",
};

/** 报告正文 + 视角切换 tab（同一天多视角同源数据，仅加权/解读不同）。 */
export default function ReportViewer({ reports }: { reports: ReportDetail[] }) {
  const [active, setActive] = useState(0);
  const report = reports[active] ?? reports[0];
  if (!report) return null;

  return (
    <div>
      {reports.length > 1 ? (
        <div className="mb-6 inline-flex gap-1 rounded-xl border border-edge bg-white/[0.03] p-1">
          {reports.map((r, i) => {
            const lens = r.lens ?? "pm";
            const on = i === active;
            return (
              <button
                key={lens}
                type="button"
                onClick={() => setActive(i)}
                className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                  on
                    ? "bg-accent-gradient text-[#06121a]"
                    : "text-zinc-400 hover:text-zinc-100"
                }`}
              >
                {LENS_LABELS[lens] ?? lens}
              </button>
            );
          })}
        </div>
      ) : null}

      <article
        className="prose prose-invert max-w-none prose-headings:tracking-tight prose-a:text-accent prose-a:no-underline hover:prose-a:underline prose-blockquote:border-l-accent/50 prose-blockquote:text-zinc-400 prose-strong:text-zinc-100 prose-hr:border-white/[0.08]"
        dangerouslySetInnerHTML={{ __html: report.html }}
      />
    </div>
  );
}
