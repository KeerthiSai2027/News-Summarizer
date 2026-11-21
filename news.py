"""Fetch news from GNews / NewsAPI and extract full article text."""
import requests
import trafilatura

GNEWS_URL = "https://gnews.io/api/v4"
NEWSAPI_URL = "https://newsapi.org/v2"
TIMEOUT = 15


def fetch_gnews(api_key, query=None, category="general", country="in",
                lang="en", max_results=10):
    if query:
        url, params = f"{GNEWS_URL}/search", {"q": query}
    else:
        url, params = f"{GNEWS_URL}/top-headlines", {"category": category, "country": country}
    params.update({"lang": lang, "max": max_results, "apikey": api_key})

    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return [
        {
            "title": a.get("title", ""),
            "description": a.get("description") or "",
            "content": a.get("content") or "",
            "url": a.get("url", ""),
            "image": a.get("image"),
            "source": (a.get("source") or {}).get("name", "Unknown"),
            "published_at": a.get("publishedAt", ""),
        }
        for a in resp.json().get("articles", [])
    ]


def fetch_newsapi(api_key, query=None, category="general", country="in",
                  max_results=10):
    params = {"pageSize": max_results, "apiKey": api_key}
    if query:
        url, params["q"], params["sortBy"], params["language"] = (
            f"{NEWSAPI_URL}/everything", query, "publishedAt", "en")
    else:
        url = f"{NEWSAPI_URL}/top-headlines"
        params.update({"category": category, "country": country})

    resp = requests.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return [
        {
            "title": a.get("title", ""),
            "description": a.get("description") or "",
            "content": a.get("content") or "",
            "url": a.get("url", ""),
            "image": a.get("urlToImage"),
            "source": (a.get("source") or {}).get("name", "Unknown"),
            "published_at": a.get("publishedAt", ""),
        }
        for a in resp.json().get("articles", [])
    ]


def get_full_text(article):
    """Scrape the full article; fall back to API snippets if scraping fails."""
    try:
        downloaded = trafilatura.fetch_url(article["url"])
        text = trafilatura.extract(downloaded, include_comments=False) if downloaded else None
        if text and len(text.split()) > 80:
            return text, True
    except Exception:
        pass
    fallback = f"{article['description']} {article['content']}".strip()
    return fallback, False
