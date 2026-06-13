import json


def test_rss_parse(fixtures):
    from app.fetchers.rss import parse_feed

    items = parse_feed((fixtures / "sample_rss.xml").read_text(), source_url="https://example.com/feed")
    assert len(items) == 2
    assert items[0].title == "Introducing SuperModel 3.0"
    assert items[0].url.startswith("https://example.com/supermodel-3")
    assert items[0].published_at is not None
    assert "SuperModel 3.0" in items[0].content  # HTML 已剥离
    assert "<p>" not in items[0].content


def test_hn_parse_filters_low_points(fixtures):
    from app.fetchers.hackernews import parse_response

    items = parse_response(json.loads((fixtures / "sample_hn.json").read_text()))
    assert len(items) == 2
    assert all(i.extra["points"] >= 100 for i in items)
    assert items[0].url == "https://github.com/example/eval-harness"


def test_reddit_parse_filters_low_score(fixtures):
    from app.fetchers.reddit import parse_listing

    items = parse_listing(json.loads((fixtures / "sample_reddit.json").read_text()))
    assert len(items) == 1
    assert items[0].extra["score"] == 980
    assert items[0].url.startswith("https://www.reddit.com/r/LocalLLaMA/")


def test_hf_papers_parse(fixtures):
    from app.fetchers.huggingface import parse_papers

    items = parse_papers(json.loads((fixtures / "sample_hf_papers.json").read_text()))
    assert len(items) == 2
    assert items[0].url == "https://huggingface.co/papers/2606.01234"
    assert items[0].published_at is not None


def test_github_trending_parse_and_ai_filter():
    from app.fetchers.github_trending import parse_trending

    html = """
    <html><body>
    <article class="Box-row">
      <h2><a href="/acme/llm-toolkit">acme / llm-toolkit</a></h2>
      <p>A toolkit for LLM agents</p>
      <a href="/acme/llm-toolkit/stargazers">1,234</a>
    </article>
    <article class="Box-row">
      <h2><a href="/foo/cooking-recipes">foo / cooking-recipes</a></h2>
      <p>Best pasta recipes</p>
      <a href="/foo/cooking-recipes/stargazers">99</a>
    </article>
    </body></html>
    """
    items = parse_trending(html)
    assert len(items) == 1
    assert items[0].url == "https://github.com/acme/llm-toolkit"
    assert items[0].extra["stars"] == "1234"


def test_hf_spaces_parse():
    from app.fetchers.huggingface import parse_spaces

    data = [
        {"id": "acme/cool-ai-app", "likes": 209, "sdk": "gradio", "createdAt": "2026-06-10T00:00:00.000Z"},
        {"id": "", "likes": 5},  # 无 id 应跳过
    ]
    items = parse_spaces(data)
    assert len(items) == 1
    assert items[0].url == "https://huggingface.co/spaces/acme/cool-ai-app"
    assert "gradio" in items[0].content


def test_fetchers_registry():
    from app.fetchers import FETCHERS

    assert {"rss", "hackernews", "github_trending", "hf_papers", "hf_models", "hf_spaces", "reddit"} <= set(FETCHERS)
    assert "rsshub" not in FETCHERS
