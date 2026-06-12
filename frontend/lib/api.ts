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
