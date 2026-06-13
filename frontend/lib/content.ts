import fs from "node:fs";
import path from "node:path";
import type {
  FeedItem,
  ReportDetail,
  ReportSummary,
  ReportType,
} from "@/lib/types";

/**
 * 构建期静态数据层：从 content/ 目录（由 backend/export_static.py 生成）读取 JSON。
 * 替代旧的运行时 API fetch —— 静态导出后站点没有后端，数据在构建期注入。
 * 所有函数仅在 Server Component / 构建期调用。
 */
const CONTENT_DIR = path.join(process.cwd(), "content");

function readJSON<T>(file: string, fallback: T): T {
  try {
    return JSON.parse(fs.readFileSync(path.join(CONTENT_DIR, file), "utf-8")) as T;
  } catch {
    return fallback;
  }
}

/** 全部报告元信息（已按 created_at 倒序）。可选按类型过滤。 */
export function getReports(type?: ReportType | string): ReportSummary[] {
  const all = readJSON<ReportSummary[]>("reports.json", []);
  return type ? all.filter((r) => r.type === type) : all;
}

/** 单份报告全文。不存在返回 null。 */
export function getReport(type: string, date: string): ReportDetail | null {
  return readJSON<ReportDetail | null>(`report-${type}-${date}.json`, null);
}

/** 某类型最新一份报告。 */
export function getLatestReport(type: ReportType | string): ReportDetail | null {
  const list = getReports(type);
  if (list.length === 0) return null;
  return getReport(list[0].type, list[0].period_date);
}

/** 全部加工条目（已按 id 倒序）。供信息流 / 搜索客户端筛选。 */
export function getItems(): FeedItem[] {
  return readJSON<FeedItem[]>("items.json", []);
}
