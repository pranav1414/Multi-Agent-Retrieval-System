import requests
import serpapi
# from serpapi import GoogleSearch
from serpapi.google_search import GoogleSearch
from bs4 import BeautifulSoup
from typing import List, Dict

def WebSearchAgent(
    query: str,
    serp_api_key: str,
    num_results: int = 5
) -> List[Dict[str, str]]:
    """
    Perform a web search using SerpApi and fetch detailed content for each result.

    Args:
        query (str): The search query (e.g., keywords or document context).
        serp_api_key (str): Your SerpApi key.
        num_results (int): Number of search results to retrieve.

    Returns:
        List[Dict[str, str]]: List of search results with title, URL, snippet, and full content.
    """
    def fetch_full_content(url: str) -> str:
        """
        Fetches full page content from a URL using BeautifulSoup.

        Args:
            url (str): URL of the page to fetch.

        Returns:
            str: Extracted full content of the page.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract content from paragraph tags
            content = "\n".join([p.text for p in soup.find_all("p")])
            return content
        except requests.RequestException as e:
            print(f"Failed to fetch content from {url}: {e}")
            return "Content not available"

    # Search using SerpApi
    params = {
        "engine": "google",
        "q": query,
        "api_key": serp_api_key,
        "num": num_results
    }
    
    search = GoogleSearch(params)
    search_results = search.get_dict()
    
    # Debug: Print raw response
    print("Raw Search Results:", search_results)
    
    if "organic_results" not in search_results or not search_results["organic_results"]:
        print("No organic results found in the search response.")
        return []

    # Process search results
    results = []
    for item in search_results["organic_results"]:
        title = item["title"]
        url = item["link"]
        snippet = item.get("snippet", "")
        
        # Fetch full content
        full_content = fetch_full_content(url)
        
        results._append({
            "title": title,
            "url": url,
            "snippet": snippet,
            "content": full_content
        })

    return results

# Single entry point
if __name__ == "__main__":
    # Configuration variables
    QUERY = "African Capital Markets Challenges and Opportunities"
    SERP_API_KEY = ""
    NUM_RESULTS = 5

    # Perform web search
    print(f"Generated Search Query: {QUERY}")
    search_results = WebSearchAgent(query=QUERY, serp_api_key=SERP_API_KEY, num_results=NUM_RESULTS)

    # Display results
    print("\nWeb Search Results with Full Content:")
    for result in search_results:
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['snippet']}")
        print(f"Content: {result['content'][:500]}...")  # Preview of content
        print("-" * 80)
