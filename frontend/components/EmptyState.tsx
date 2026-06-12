export default function EmptyState({
  message = "后端未连接或暂无数据",
  hint = "请确认后端服务已启动（默认 http://localhost:8000），稍后刷新重试。",
}: {
  message?: string;
  hint?: string;
}) {
  return (
    <div className="glass-card border-dashed px-6 py-16 text-center">
      <div className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500/20 via-blue-500/20 to-cyan-400/20 text-lg">
        ∅
      </div>
      <p className="text-base text-zinc-400">{message}</p>
      {hint ? <p className="mt-2 text-sm text-zinc-600">{hint}</p> : null}
    </div>
  );
}
