import os
from tavily import TavilyClient
from app.cache import with_cache

@with_cache
def tavily_web_search(query: str, max_results: int = 5) -> list:
    """Queries the live web using the Tavily Search API (Tier 2)."""
    api_key = os.getenv("TAVILY_API_KEY", "tvly-dummy-key")
    
    # If no real API key is provided, return a simulated result
    if api_key == "tvly-dummy-key" or not api_key:
        print(f"Tavily Web Search skipped (no API key). Returning simulated results for: {query}")
        return [
            {
                "title": f"Web coverage for: {query}",
                "snippet": f"Simulated online metrics retrieved for target topic: {query}. Market sentiment reflects positive adoption of core initiatives.",
                "url": "https://www.marketwatch.com",
                "source": "Web Search (Simulated)"
            }
        ]
        
    try:
        client = TavilyClient(api_key=api_key)
        # Using search depth basic to minimize latency
        response = client.search(query=query, search_depth="basic", max_results=max_results)
        
        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "snippet": r.get("content", ""),
                "url": r.get("url", ""),
                "source": "Tavily Web Search"
            })
        return results
    except Exception as e:
        print(f"Tavily Search failed: {str(e)}")
        return [
            {
                "title": f"Search Error: {query}",
                "snippet": f"Failed to retrieve live web data due to API error: {str(e)}",
                "url": "",
                "source": "Error"
            }
        ]
