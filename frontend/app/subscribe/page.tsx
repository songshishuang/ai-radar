"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";

const FREQ_OPTIONS = [
  { value: "daily", label: "日报", desc: "每天一封，速览过去 24 小时" },
  { value: "weekly", label: "周报", desc: "每周一封，提炼一周趋势" },
  { value: "monthly", label: "月报", desc: "每月一封，纵览行业大局" },
];

type Status = "idle" | "loading" | "success" | "error";

export default function SubscribePage() {
  const [email, setEmail] = useState("");
  const [frequencies, setFrequencies] = useState<string[]>(["daily"]);
  const [status, setStatus] = useState<Status>("idle");
  const [errorMsg, setErrorMsg] = useState("");

  function toggleFrequency(value: string) {
    setFrequencies((prev) =>
      prev.includes(value)
        ? prev.filter((f) => f !== value)
        : [...prev, value]
    );
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (frequencies.length === 0) {
      setStatus("error");
      setErrorMsg("请至少选择一种订阅频率。");
      return;
    }
    setStatus("loading");
    setErrorMsg("");
    try {
      const res = await fetch(`${API_BASE}/api/subscriptions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, frequencies }),
      });
      if (!res.ok) {
        let msg = `提交失败（HTTP ${res.status}）`;
        try {
          const data: unknown = await res.json();
          if (
            data &&
            typeof data === "object" &&
            "detail" in data &&
            typeof (data as { detail: unknown }).detail === "string"
          ) {
            msg = (data as { detail: string }).detail;
          }
        } catch {
          // 响应体不是 JSON，保留默认错误信息
        }
        throw new Error(msg);
      }
      setStatus("success");
    } catch (err) {
      setStatus("error");
      setErrorMsg(
        err instanceof TypeError
          ? "无法连接后端服务，请确认后端已启动后重试。"
          : err instanceof Error
            ? err.message
            : "提交失败，请稍后重试。"
      );
    }
  }

  return (
    <div className="mx-auto max-w-lg pt-6">
      <h1 className="text-gradient mb-2 inline-block text-2xl font-bold tracking-tight">
        订阅报告
      </h1>
      <p className="mb-8 text-sm text-zinc-500">
        留下邮箱，AI 情报报告定期送达。
      </p>

      {status === "success" ? (
        <div className="glass-card px-6 py-12 text-center">
          {/* CSS 打勾动画 */}
          <svg
            viewBox="0 0 56 56"
            className="check-circle mx-auto mb-5 h-14 w-14"
            aria-hidden
          >
            <defs>
              <linearGradient id="check-grad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#8b5cf6" />
                <stop offset="50%" stopColor="#3b82f6" />
                <stop offset="100%" stopColor="#22d3ee" />
              </linearGradient>
            </defs>
            <circle
              cx="28"
              cy="28"
              r="26"
              fill="none"
              stroke="url(#check-grad)"
              strokeWidth="2.5"
            />
            <path
              className="check-path"
              d="M17 28.5 L25 36 L39 21"
              fill="none"
              stroke="url(#check-grad)"
              strokeWidth="3.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <p className="text-lg font-semibold text-zinc-50">
            订阅成功，请查收确认邮件
          </p>
          <p className="mt-2 text-sm text-zinc-400">
            已为 <span className="text-cyan-300">{email}</span> 开通：
            {FREQ_OPTIONS.filter((o) => frequencies.includes(o.value))
              .map((o) => o.label)
              .join("、")}
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="glass-card space-y-6 p-6">
          <div>
            <label
              htmlFor="email"
              className="mb-1.5 block text-sm font-medium text-zinc-300"
            >
              邮箱地址
            </label>
            <div className="rounded-xl bg-white/10 p-px transition focus-within:bg-gradient-to-r focus-within:from-violet-500 focus-within:via-blue-500 focus-within:to-cyan-400">
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full rounded-[11px] bg-[#101016] px-4 py-2.5 text-sm text-zinc-200 outline-none placeholder:text-zinc-600"
              />
            </div>
          </div>

          <fieldset>
            <legend className="mb-2 text-sm font-medium text-zinc-300">
              订阅频率（可多选）
            </legend>
            <div className="space-y-2">
              {FREQ_OPTIONS.map((opt) => {
                const checked = frequencies.includes(opt.value);
                return (
                  <label
                    key={opt.value}
                    className={`flex cursor-pointer items-start gap-3 rounded-xl border px-4 py-3 transition ${
                      checked
                        ? "border-violet-400/50 bg-violet-500/[0.08]"
                        : "border-white/10 hover:border-white/25 hover:bg-white/[0.03]"
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleFrequency(opt.value)}
                      className="mt-0.5 h-4 w-4 rounded accent-violet-500"
                    />
                    <span>
                      <span className="block text-sm font-medium text-zinc-100">
                        {opt.label}
                      </span>
                      <span className="block text-xs text-zinc-500">
                        {opt.desc}
                      </span>
                    </span>
                  </label>
                );
              })}
            </div>
          </fieldset>

          {status === "error" && errorMsg ? (
            <p className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2.5 text-sm text-red-400">
              {errorMsg}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={status === "loading"}
            className="bg-accent-gradient w-full rounded-xl px-4 py-2.5 text-sm font-semibold text-white transition hover:opacity-90 hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {status === "loading" ? "提交中…" : "订阅"}
          </button>
        </form>
      )}
    </div>
  );
}
