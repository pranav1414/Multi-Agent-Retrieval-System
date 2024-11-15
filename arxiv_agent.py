import requests
from typing import List, Dict
from bs4 import BeautifulSoup


class ArxivAgent:
    def __init__(self, base_url="http://export.arxiv.org/api/query"):
        self.base_url = base_url

    def search_arxiv(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Search for research papers on Arxiv based on a query.
        
        Args:
            query (str): Search query, such as keywords or document topics.
            max_results (int): Number of results to return.

        Returns:
            List[Dict[str, str]]: List of dictionaries containing paper info.
        """
        # Prepare the query parameters
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results
        }
        
        # Send the request to Arxiv API
        response = requests.get(self.base_url, params=params)
        
        if response.status_code == 200:
            # Parse the XML response
            papers = self.parse_arxiv_response(response.text)
            return papers
        else:
            print(f"Failed to fetch results from Arxiv. Status code: {response.status_code}")
            return []

    def parse_arxiv_response(self, xml_response: str) -> List[Dict[str, str]]:
        """
        Parse the XML response from Arxiv API to extract relevant paper information.
        
        Args:
            xml_response (str): XML response from Arxiv API.

        Returns:
            List[Dict[str, str]]: List of dictionaries with paper details.
        """
        import xml.etree.ElementTree as ET
        
        root = ET.fromstring(xml_response)
        papers = []
        
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title").text
            summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
            link = entry.find("{http://www.w3.org/2005/Atom}id").text
            authors = ", ".join(
                author.find("{http://www.w3.org/2005/Atom}name").text
                for author in entry.findall("{http://www.w3.org/2005/Atom}author")
            )
            
            papers.append({
                "title": title.strip(),
                "summary": summary.strip(),
                "authors": authors,
                "link": link
            })
        
        return papers

    def fetch_page_content(self, url: str) -> str:
        """
        Fetches the full page content of the given URL.
        
        Args:
            url (str): URL of the paper's page.

        Returns:
            str: Extracted text content from the page.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract content from the main article text
            content = "\n".join(p.text for p in soup.find_all("p"))
            return content
        except requests.RequestException as e:
            print(f"Failed to fetch content from {url}: {e}")
            return "Content not available"


# Example Usage
if __name__ == "__main__":
    arxiv_agent = ArxivAgent()
    
    # Sample query from a selected document's topic or keywords
    query = "African Capital Markets Challenges and Opportunities multimodal"  # Replace with keywords from document
    results = arxiv_agent.search_arxiv(query)
    
    # Display results and fetch content
    for paper in results:
        print(f"Title: {paper['title']}")
        print(f"Authors: {paper['authors']}")
        print(f"Summary: {paper['summary'][:200]}...")  # Show only the first 200 characters of the summary
        print(f"Link: {paper['link']}")
        
        # Fetch and display content from the paper's page
        content = arxiv_agent.fetch_page_content(paper['link'])
        print(f"Content (Preview): {content[:500]}...")  # Show only the first 500 characters of the content
        print("-" * 80)
