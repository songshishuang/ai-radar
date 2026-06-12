/** 报告类型 */
export type ReportType = "daily" | "weekly" | "monthly";

/** GET /api/reports 列表项 */
export interface ReportSummary {
  id: number | string;
  type: string;
  period_date: string;
  title: string;
  created_at: string;
}

/** GET /api/reports/{type}/{period_date} 详情 */
export interface ReportDetail extends ReportSummary {
  markdown: string;
  /** 完整报告正文 HTML 字符串 */
  html: string;
  /** JSON 字符串 */
  headline_analysis: string;
  stats: unknown;
}

/** GET /api/items 信息流条目 */
export interface FeedItem {
  id: number | string;
  title: string;
  url: string;
  source: string;
  published_at: string;
  summary_zh: string;
  category: string;
  tags: string[];
  importance_score: number;
}
