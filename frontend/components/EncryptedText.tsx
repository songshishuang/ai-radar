"use client";

import { useEffect, useState } from "react";

const GLYPHS = "ABCDEF0123456789!<>-_\\/[]{}=+*^?#________";

/**
 * 加密解码效果：乱码逐字解析为真文本（"decrypting" 观感）。纯 React + setInterval，零依赖。
 * 适合 latin/数字小标签（日期、// LIVE、kicker），CJK 也可用但宽度会跳。
 */
export default function EncryptedText({
  text,
  className,
  durationMs = 900,
}: {
  text: string;
  className?: string;
  durationMs?: number;
}) {
  const [display, setDisplay] = useState(text);

  useEffect(() => {
    const chars = Array.from(text);
    const totalFrames = Math.max(1, Math.ceil(durationMs / 40));
    let frame = 0;
    const id = setInterval(() => {
      frame += 1;
      const revealed = Math.floor((frame / totalFrames) * chars.length);
      setDisplay(
        chars
          .map((ch, i) =>
            i < revealed || ch === " "
              ? ch
              : GLYPHS[Math.floor(Math.random() * GLYPHS.length)]
          )
          .join("")
      );
      if (frame >= totalFrames) {
        setDisplay(text);
        clearInterval(id);
      }
    }, 40);
    return () => clearInterval(id);
  }, [text, durationMs]);

  return (
    <span className={className} aria-label={text}>
      {display}
    </span>
  );
}
