from src.tools.tools import web_search, scrape_url
import re

raw_search = web_search.invoke({"query": "Pakistan history"})
print("Raw search length:", len(raw_search))

urls = re.findall(r"https?://[^\s\)\"\'\<\>]+", raw_search)
print("Extracted URLs count:", len(urls))
print("URLs:", urls)

if urls:
    scraped = scrape_url.invoke({"url": urls[0]})
    print("Scraped from", urls[0], "length:", len(scraped))
    print("Scraped preview:", scraped[:200])

