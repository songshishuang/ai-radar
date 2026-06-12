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
  /** headline_analysis：JSON 字符串（HeadlineAnalysis[]），用 parseHeadlines 解析 */
  headline_analysis: string;
  /** stats：JSON 字符串或对象（ReportStats），用 parseReportStats 解析 */
  stats: unknown;
}

/** headline_analysis JSON 数组单条（今日必读） */
export interface HeadlineAnalysis {
  headline: string;
  /** 一句话结论（V3 起；旧报告无此字段，渲染需兜底 background 首句） */
  so_what?: string;
  background: string;
  industry_impact: string;
  competitive: string;
  rd_efficiency: string;
  biz_opportunity: string;
  action_items: string[];
  item_id?: number | string;
  url: string;
  source: string;
  importance: number;
}

/** 报告 stats JSON 结构 */
export interface ReportStats {
  total?: number;
  /** 当日速览，可能缺失（缺失时取 markdown 前 200 字兜底） */
  tldr?: string;
  by_category?: Record<string, number>;
  degraded_sources?: string[];
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
  /** 公司 / 产品名实体（旧数据可能缺失，渲染需兜底） */
  entities?: string[];
}
