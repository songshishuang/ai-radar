"use client";

/**
 * 逐字淡入（视觉上像 LLM 流式输出）。纯 CSS 关键帧 word-in，零依赖。
 * 适合首页速览/标题等短文本——让站「读起来是 AI 生成的」。
 */
export default function TextGenerate({
  text,
  className,
  stagger = 0.016,
}: {
  text: string;
  className?: string;
  stagger?: number;
}) {
  const chars = Array.from(text);
  return (
    <span className={className} aria-label={text}>
      {chars.map((ch, i) => (
        <span
          key={i}
          aria-hidden
          style={{
            display: "inline-block",
            whiteSpace: ch === " " ? "pre" : undefined,
            animation: "word-in 0.5s ease both",
            animationDelay: `${i * stagger}s`,
          }}
        >
          {ch}
        </span>
      ))}
    </span>
  );
}
