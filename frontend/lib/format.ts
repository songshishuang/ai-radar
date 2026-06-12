/** "2026-06-12T08:30:00" → "2026-06-12 08:30"（字符串截取，规避时区/ICU 差异） */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "";
  return String(value).replace("T", " ").slice(0, 16);
}

/** 取日期部分 "2026-06-12" */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "";
  return String(value).slice(0, 10);
}

/** searchParams 值可能是 string | string[]，统一取第一个 */
export function firstParam(
  value: string | string[] | undefined
): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}
