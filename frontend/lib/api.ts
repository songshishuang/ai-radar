import type { HeadlineAnalysis, ReportStats } from "@/lib/types";

/**
 * 后端 API 访问封装。
 * BASE 优先取 NEXT_PUBLIC_API_BASE（Server / Client 两侧均可用），默认本地 FastAPI。
 */
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

/**
 * GET 请求并解析 JSON。开发期实时：cache: 'no-store'。
 * 失败（网络错误 / 非 2xx）一律 throw，由页面侧 try/catch 渲染空态。
 */
export async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API 请求失败 ${res.status}: ${path}`);
  }
  return (await res.json()) as T;
}

/** 兼容「JSON 字符串」与「已是对象」两种形态的安全解析 */
function safeParse(raw: unknown): unknown {
  if (typeof raw !== "string") return raw;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/** 解析报告 stats（JSON 字符串 / 对象均可），失败返回 null */
export function parseReportStats(raw: unknown): ReportStats | null {
  const v = safeParse(raw);
  if (v && typeof v === "object" && !Array.isArray(v)) {
    return v as ReportStats;
  }
  return null;
}

/** 解析 headline_analysis（今日必读 JSON 数组），失败返回 [] */
export function parseHeadlines(raw: unknown): HeadlineAnalysis[] {
  const v = safeParse(raw);
  if (!Array.isArray(v)) return [];
  return v.filter(
    (it): it is HeadlineAnalysis =>
      !!it && typeof it === "object" && typeof it.headline === "string"
  );
}

/** 从 markdown 提取纯文本摘要（stats.tldr 缺失时的兜底），默认 200 字 */
export function markdownExcerpt(markdown: string, maxLen = 200): string {
  const text = markdown
    .replace(/```[\s\S]*?```/g, " ") // 代码块
    .replace(/^#{1,6}\s*/gm, "") // 标题井号
    .replace(/^>\s*/gm, "") // 引用
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1") // 图片
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1") // 链接保留文字
    .replace(/[*_`~#|-]/g, " ") // 行内符号
    .replace(/\s+/g, " ")
    .trim();
  return text.length > maxLen ? `${text.slice(0, maxLen)}…` : text;
}
