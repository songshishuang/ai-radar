export default function EmptyState({
  message = "后端未连接或暂无数据",
  hint = "请确认后端服务已启动（默认 http://localhost:8000），稍后刷新重试。",
}: {
  message?: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-dashed border-gray-300 bg-white px-6 py-16 text-center">
      <p className="text-base text-gray-500">{message}</p>
      {hint ? <p className="mt-2 text-sm text-gray-400">{hint}</p> : null}
    </div>
  );
}
