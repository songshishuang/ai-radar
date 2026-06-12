import pytest

from app.llm import ClaudeCLIProvider, LLMError, MockProvider, complete_json


def test_mock_complete_json_with_fence():
    p = MockProvider(responses=['```json\n[{"id": 1, "summary_zh": "测试"}]\n```'])
    out = complete_json(p, "prompt", tier="fast")
    assert out[0]["summary_zh"] == "测试"


def test_complete_json_bare():
    p = MockProvider(responses=['{"ok": true}'])
    assert complete_json(p, "x") == {"ok": True}


def test_complete_json_with_prefix_text():
    p = MockProvider(responses=['好的，结果如下：[{"id": 2}] 以上。'])
    assert complete_json(p, "x")[0]["id"] == 2


def test_complete_json_retries_once_then_raises():
    p = MockProvider(responses=["not json at all", "still not json"])
    with pytest.raises(LLMError):
        complete_json(p, "x")
    assert len(p.calls) == 2
    assert "只输出合法 JSON" in p.calls[1]["prompt"]


def test_claude_cli_command_shape(monkeypatch):
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"] = cmd
        captured["input"] = kw.get("input")

        class R:
            returncode = 0
            stdout = '{"ok": true}'
            stderr = ""

        return R()

    monkeypatch.setattr("subprocess.run", fake_run)
    p = ClaudeCLIProvider()
    out = p.complete("hello world", tier="deep")
    assert out == '{"ok": true}'
    assert "--model" in captured["cmd"]
    assert captured["input"] == "hello world"


def test_claude_cli_nonzero_raises(monkeypatch):
    def fake_run(cmd, **kw):
        class R:
            returncode = 1
            stdout = ""
            stderr = "boom"

        return R()

    monkeypatch.setattr("subprocess.run", fake_run)
    with pytest.raises(LLMError):
        ClaudeCLIProvider().complete("x")
