from typing import Any

import httpx


async def search_tavily(query: str, api_key: str, timeout: float, max_results: int) -> list[dict[str, Any]]:
    if not api_key:
        return []
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            "https://api.tavily.com/search",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
                "include_images": False,
            },
        )
        response.raise_for_status()
    items = response.json().get("results", [])
    return [
        {
            "title": str(item.get("title", "")).strip(),
            "url": str(item.get("url", "")).strip(),
            "snippet": str(item.get("content", "")).strip(),
            "published_at": item.get("published_date"),
            "provider": "tavily",
            "score": float(item.get("score", 0)),
        }
        for item in items
        if item.get("title") and item.get("url")
    ]
