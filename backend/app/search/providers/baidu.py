import html
import re
from typing import Any
from urllib.parse import quote_plus

import httpx


RESULT_PATTERN = re.compile(
    r'<h3[^>]*class="[^"]*t[^"]*"[^>]*>.*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?</h3>(.*?)(?=<h3|$)',
    re.IGNORECASE | re.DOTALL,
)
TAG_PATTERN = re.compile(r"<[^>]+>")


def parse_baidu_results(document: str, max_results: int) -> list[dict[str, Any]]:
    results = []
    for url, raw_title, tail in RESULT_PATTERN.findall(document):
        title = html.unescape(TAG_PATTERN.sub("", raw_title)).strip()
        snippet = html.unescape(TAG_PATTERN.sub(" ", tail))
        snippet = re.sub(r"\s+", " ", snippet).strip()[:500]
        if title and url.startswith(("http://", "https://")):
            results.append({
                "title": title, "url": html.unescape(url), "snippet": snippet,
                "published_at": None, "provider": "baidu", "score": 0.5,
            })
        if len(results) >= max_results:
            break
    return results


async def search_baidu(query: str, timeout: float, max_results: int) -> list[dict[str, Any]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
        response = await client.get(f"https://www.baidu.com/s?wd={quote_plus(query)}&rn={max_results}")
        response.raise_for_status()
    return parse_baidu_results(response.text, max_results)
