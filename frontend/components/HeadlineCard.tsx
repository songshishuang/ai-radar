"use client";

import { useState } from "react";
import ScoreBadge from "@/components/ScoreBadge";
import type { HeadlineAnalysis } from "@/lib/types";

const SECTIONS: { key: keyof HeadlineAnalysis; label: string }[] = [
  { key: "background", label: "事件背景" },
  { key: "industry_impact", label: "行业影响" },
  { key: "competitive", label: "竞争格局" },
  { key: "rd_efficiency", label: "研发提效" },
  { key: "biz_opportunity", label: "商业机会" },
];

/** 今日必读卡：默认 headline + ⚡so-what 一句话结论，点击展开六段全文 */
export default function HeadlineCard({ item }: { item: HeadlineAnalysis }) {
  const [open, setOpen] = useState(false);
  const actionItems = Array.isArray(item.action_items)
    ? item.action_items
    : [];

  return (
    <article className="glass-card card-hover accent-left overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="block w-full px-5 py-4 text-left"
      >
        <div className="flex items-start justify-between gap-3">
          <h3 className="font-semibold leading-snug text-zinc-50">
            {item.headline}
          </h3>
          <div className="flex shrink-0 items-center gap-2">
            <ScoreBadge score={item.importance} />
            <span
              aria-hidden
              className={`text-zinc-500 transition-transform duration-200 ${
                open ? "rotate-180" : ""
              }`}
            >
              ▾
            </span>
          </div>
        </div>
        {item.so_what || item.background ? (
          <p className="mt-2 text-sm leading-relaxed text-cyan-200/90">
            <span aria-hidden className="mr-1">⚡</span>
            {item.so_what ?? item.background?.split("。")[0] + "。"}
          </p>
        ) : null}
      </button>

      {/* 纯 CSS 展开动画：grid-rows 0fr → 1fr */}
      <div
        className={`grid transition-[grid-template-rows] duration-300 ease-out ${
          open ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        }`}
      >
        <div className="overflow-hidden">
          <div className="space-y-4 border-t border-white/[0.06] px-5 py-4">
            {SECTIONS.map(({ key, label }) => {
              const text = item[key];
              if (typeof text !== "string" || !text) return null;
              return (
                <section key={key}>
                  <h4 className="mb-1 text-xs font-semibold uppercase tracking-wider text-gradient-soft">
                    {label}
                  </h4>
                  <p className="text-sm leading-relaxed text-zinc-300">
                    {text}
                  </p>
                </section>
              );
            })}

            {actionItems.length > 0 ? (
              <section>
                <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-gradient-soft">
                  行动建议
                </h4>
                <ul className="space-y-1.5">
                  {actionItems.map((action, i) => (
                    <li
                      key={i}
                      className="flex gap-2 text-sm leading-relaxed text-zinc-300"
                    >
                      <span className="mt-[7px] h-1 w-1 shrink-0 rounded-full bg-cyan-400" />
                      {action}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            <div className="flex items-center gap-2 pt-1 text-xs text-zinc-500">
              {item.source ? <span>{item.source}</span> : null}
              {item.url ? (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="text-cyan-400/80 transition-colors hover:text-cyan-300"
                >
                  阅读原文 ↗
                </a>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
