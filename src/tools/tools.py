from langchain.tools import tool
from dotenv import load_dotenv
from tavily import TavilyClient
from rich import print
from bs4 import BeautifulSoup
from readability import Document
import trafilatura
import requests
import os
import re

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def web_search(query: str) -> str:
    """
    Search the web for the given query and return the results.
    Args:
        query (str): The query to search for.
    Returns:
        str: The results of the search.
    """ 
    results = tavily.search(query=query, max_results=5)

    out = []

    for r in results.get("results", []):
        out.append(f"Title: {r['title']}\n URL: {r['url']}\n Content: {r['content'][:300]}\n")     
    
    return "\n----\n".join(out)       
    
@tool    
def scrape_url(url: str) -> str:
    """
    Fetch a webpage and extract only the main content using trafilatura.

    Args:
        url (str): The URL of the webpage to fetch.

    Returns:
        str: Cleaned text content of the webpage, or error message.
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        # Fetch the webpage content with custom headers to prevent 403 Forbidden errors
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # trafilatura.extract parses HTML and strips boilerplate (ads, navbars, footers)
        text = trafilatura.extract(
            response.text,
            include_links=False,
            include_comments=False,
            include_tables=True,
        )
        
        # Fallback to readability/BeautifulSoup if trafilatura returns nothing
        if not text:
            doc = Document(response.text)
            soup = BeautifulSoup(doc.summary(), "html.parser")
            text = soup.get_text(separator="\n")

        if not text:
            return "Failed to extract content from the webpage."
        
        # Normalize excessive newlines while keeping paragraph breaks
        cleaned = re.sub(r"\n{3,}", "\n\n", text).strip()
        
        return cleaned
        
    except requests.exceptions.RequestException as e:
        return f"Error fetching webpage: {str(e)}"
    except Exception as e:
        return f"Error processing webpage: {str(e)}"
