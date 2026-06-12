/** 分类枚举（8 类）→ 中文名 */
export const CATEGORY_LABELS: Record<string, string> = {
  "model-release": "模型发布",
  "dev-tooling": "产研工具",
  "agent-infra": "Agent基建",
  research: "前沿研究",
  opensource: "开源生态",
  "product-launch": "产品动态",
  business: "商业资本",
  "policy-safety": "政策安全",
};

/** 旧四类（可能短暂残留在数据中）兜底映射 */
export const LEGACY_CATEGORY_LABELS: Record<string, string> = {
  paradigm: "产研AI范式",
  tech: "AI技术",
  product: "行业AI产品",
  // opensource 与新枚举同 key，自然命中新映射
};

/** 分类 → 中文名；新 8 类优先，旧 4 类兜底，未知值显示原值（不崩） */
export function categoryLabel(category: string | null | undefined): string {
  if (!category) return "";
  return (
    CATEGORY_LABELS[category] ?? LEGACY_CATEGORY_LABELS[category] ?? category
  );
}

/** 报告类型 → 中文名 */
export const REPORT_TYPE_LABELS: Record<string, string> = {
  daily: "日报",
  weekly: "周报",
  monthly: "月报",
};

export const REPORT_TYPES = ["daily", "weekly", "monthly"] as const;
