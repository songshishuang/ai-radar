/** 分类枚举 → 中文名 */
export const CATEGORY_LABELS: Record<string, string> = {
  paradigm: "产研AI范式",
  tech: "AI技术",
  opensource: "开源项目",
  product: "行业AI产品",
};

/** 报告类型 → 中文名 */
export const REPORT_TYPE_LABELS: Record<string, string> = {
  daily: "日报",
  weekly: "周报",
  monthly: "月报",
};

export const REPORT_TYPES = ["daily", "weekly", "monthly"] as const;
