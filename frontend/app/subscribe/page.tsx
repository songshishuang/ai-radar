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
    <div className="mx-auto max-w-lg">
      <h1 className="mb-2 text-2xl font-bold tracking-tight">订阅报告</h1>
      <p className="mb-8 text-sm text-gray-500">
        留下邮箱，AI 情报报告定期送达。
      </p>

      {status === "success" ? (
        <div className="rounded-lg border border-green-200 bg-green-50 px-6 py-10 text-center">
          <p className="text-lg font-medium text-green-700">
            订阅成功，请查收确认邮件
          </p>
          <p className="mt-2 text-sm text-green-600">
            已为 {email} 开通：
            {FREQ_OPTIONS.filter((o) => frequencies.includes(o.value))
              .map((o) => o.label)
              .join("、")}
          </p>
        </div>
      ) : (
        <form
          onSubmit={handleSubmit}
          className="space-y-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm"
        >
          <div>
            <label
              htmlFor="email"
              className="mb-1.5 block text-sm font-medium text-gray-700"
            >
              邮箱地址
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full rounded-md border border-gray-300 px-4 py-2 text-sm shadow-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>

          <fieldset>
            <legend className="mb-2 text-sm font-medium text-gray-700">
              订阅频率（可多选）
            </legend>
            <div className="space-y-2">
              {FREQ_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className="flex cursor-pointer items-start gap-3 rounded-md border border-gray-200 px-4 py-3 hover:bg-gray-50"
                >
                  <input
                    type="checkbox"
                    checked={frequencies.includes(opt.value)}
                    onChange={() => toggleFrequency(opt.value)}
                    className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span>
                    <span className="block text-sm font-medium text-gray-900">
                      {opt.label}
                    </span>
                    <span className="block text-xs text-gray-500">
                      {opt.desc}
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          {status === "error" && errorMsg ? (
            <p className="rounded-md bg-red-50 px-4 py-2.5 text-sm text-red-600">
              {errorMsg}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={status === "loading"}
            className="w-full rounded-md bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {status === "loading" ? "提交中…" : "订阅"}
          </button>
        </form>
      )}
    </div>
  );
}
