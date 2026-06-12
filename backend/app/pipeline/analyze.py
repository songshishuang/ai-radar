"""深度分析：对高分条目逐条生成 PM 视角研报（deep tier / Sonnet）。"""

from sqlalchemy.orm import Session

from app.llm import LLMError, LLMProvider, complete_json
from app.models import Enrichment, Item

DEEP_PROMPT = """你是资深产品经理出身的 AI 行业分析师，为一位关注「产研提效」与「商业产品机会」的 PM 写深度解读。

事件标题：{title}
中文摘要：{summary_zh}
原文要点：{content}
来源：{source}（重要度 {importance}/10）

输出 JSON（只输出 JSON，无其他文字）：
{{"headline": "<中文标题，不超过30字>",
 "background": "<事件背景，2-3句>",
 "industry_impact": "<产业影响，2-3句>",
 "competitive": "<竞品对位分析，2-3句>",
 "rd_efficiency": "<对产研提效的启示，给到可落地动作>",
 "biz_opportunity": "<商业产品机会信号>",
 "action_items": ["<PM 本周可做的具体动作>", "<动作2>"]}}"""

REQUIRED_KEYS = {"headline", "background", "industry_impact", "competitive", "rd_efficiency", "biz_opportunity", "action_items"}


def deep_analyze_one(provider: LLMProvider, item: Item, enrichment: Enrichment, source_name: str) -> dict:
    prompt = DEEP_PROMPT.format(
        title=item.title,
        summary_zh=enrichment.summary_zh,
        content=(item.raw_content or "")[:1500],
        source=source_name,
        importance=enrichment.importance_score,
    )
    result = complete_json(provider, prompt, tier="deep")
    if not isinstance(result, dict) or not REQUIRED_KEYS <= set(result):
        raise LLMError(f"deep analysis missing keys: {set(result) if isinstance(result, dict) else type(result)}")
    result["item_id"] = item.id
    result["url"] = item.url
    result["source"] = source_name
    result["importance"] = enrichment.importance_score
    return result


def deep_analyze(
    session: Session,
    provider: LLMProvider,
    scored: list[tuple[Item, Enrichment, str]],
    top_n: int = 5,
    min_score: int = 7,
) -> list[dict]:
    """scored: (item, enrichment, source_name)，按 importance 降序取 Top N 做深度分析。
    单条失败跳过不阻塞；全部失败返回空列表（报告侧降级为高分清单）。"""
    candidates = [t for t in scored if t[1].importance_score >= min_score]
    candidates.sort(key=lambda t: t[1].importance_score, reverse=True)
    analyses = []
    for item, enr, source_name in candidates[:top_n]:
        try:
            analyses.append(deep_analyze_one(provider, item, enr, source_name))
        except LLMError:
            continue
    return analyses
