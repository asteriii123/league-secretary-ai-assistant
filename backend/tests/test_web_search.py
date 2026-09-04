import pytest

from app.search.providers.baidu import parse_baidu_results
from app.search.service import merge_results, normalize_url


def test_normalize_url_removes_tracking_and_fragment() -> None:
    assert normalize_url("HTTPS://Example.COM/a/?utm_source=x&id=2#part") == "https://example.com/a?id=2"


def test_merge_results_deduplicates_and_orders_by_score() -> None:
    groups = [[
        {"title": "A", "url": "https://a.test/?utm_source=x", "snippet": "a", "score": .4},
    ], [
        {"title": "A2", "url": "https://a.test", "snippet": "duplicate", "score": .8},
        {"title": "B", "url": "https://b.test", "snippet": "b", "score": .7},
    ]]
    results = merge_results(groups, 8)
    assert [item["title"] for item in results] == ["B", "A"]


def test_parse_baidu_results_extracts_title_url_and_snippet() -> None:
    document = '<h3 class="t"><a href="https://example.com">示例<b>标题</b></a></h3><div>摘要内容</div>'
    result = parse_baidu_results(document, 5)
    assert result[0]["title"] == "示例标题"
    assert result[0]["url"] == "https://example.com"
    assert "摘要内容" in result[0]["snippet"]
