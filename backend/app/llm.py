"""LLM Provider 抽象：claude-cli（本地订阅）/ anthropic-api（生产）/ mock（测试）。"""

import json
import re
import subprocess
from typing import Any, Protocol

from app.config import settings


class LLMError(Exception):
    pass


class LLMProvider(Protocol):
    def complete(self, prompt: str, tier: str = "fast") -> str: ...


def _model_for(tier: str) -> str:
    return settings.llm_fast_model if tier == "fast" else settings.llm_deep_model


class ClaudeCLIProvider:
    """subprocess 调 claude CLI 非交互模式，prompt 走 stdin（避免 argv 长度限制）。"""

    def complete(self, prompt: str, tier: str = "fast") -> str:
        cmd = [
            "claude",
            "-p",
            "--model",
            _model_for(tier),
            "--max-turns",
            "1",
        ]
        try:
            r = subprocess.run(
                cmd, input=prompt, capture_output=True, text=True, timeout=600
            )
        except subprocess.TimeoutExpired as e:
            raise LLMError(f"claude CLI timeout: {e}") from e
        if r.returncode != 0:
            raise LLMError(f"claude CLI exit {r.returncode}: {r.stderr[:500]}")
        out = r.stdout.strip()
        # claude 未登录/凭证失效时仍返回 exit 0 + 提示文本（如 launchd 无头环境读不到 keychain），
        # 必须识别为失败，否则 "Not logged in" 被当作 LLM 输出 → 下游 JSON 解析炸成 failed_batches。
        low = out.lower()
        if not out or "not logged in" in low or "please run /login" in low or "invalid api key" in low:
            raise LLMError(f"claude CLI 未认证或空输出: {out[:160]!r}")
        return out


class AnthropicAPIProvider:
    def complete(self, prompt: str, tier: str = "fast") -> str:
        import anthropic

        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = client.messages.create(
            model=_model_for(tier),
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if b.type == "text")


class MockProvider:
    def __init__(self, responses: list[str] | None = None):
        self.responses = list(responses or [])
        self.calls: list[dict] = []

    def complete(self, prompt: str, tier: str = "fast") -> str:
        self.calls.append({"prompt": prompt, "tier": tier})
        if not self.responses:
            raise LLMError("MockProvider exhausted")
        return self.responses.pop(0)


def get_provider() -> LLMProvider:
    if settings.llm_provider == "claude-cli":
        return ClaudeCLIProvider()
    if settings.llm_provider == "anthropic-api":
        return AnthropicAPIProvider()
    return MockProvider()


def _extract_json(text: str) -> Any:
    """容忍 ```json fence、前后缀文字；提取首个 JSON 数组/对象。"""
    fence = re.search(r"```(?:json)?\s*(.+?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 退路：找首个 [ 或 { 起的可解析片段
    for start_ch, end_ch in (("[", "]"), ("{", "}")):
        start = text.find(start_ch)
        end = text.rfind(end_ch)
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue
    raise LLMError(f"un-parseable JSON: {text[:200]}")


def complete_json(provider: LLMProvider, prompt: str, tier: str = "fast") -> Any:
    """调用 LLM 并解析 JSON；解析失败追加严格指令重试一次。"""
    out = provider.complete(prompt, tier=tier)
    try:
        return _extract_json(out)
    except LLMError:
        retry_prompt = prompt + "\n\n重要：只输出合法 JSON，不要任何其他文字、不要 markdown 代码块。"
        out = provider.complete(retry_prompt, tier=tier)
        return _extract_json(out)
