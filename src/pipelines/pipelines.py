import sys
import re

# Ensure Windows terminal handles UTF-8 characters without charmap errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.agents.agents import build_search_agent, build_reader_agent, writer_chain, critic_chain


def _get_text(content) -> str:
    """Extract plain text whether content is a string or a list of structured content blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
        return "\n".join(parts)
    return str(content)


def _extract_all_urls(messages) -> list[str]:
    """Extract unique HTTP/HTTPS URLs from all messages and tool outputs."""
    urls = []
    url_pattern = re.compile(r"https?://[^\s\)\"\'\<\>]+", re.IGNORECASE)

    for msg in messages:
        # Check direct message content
        content = getattr(msg, "content", "")
        text = _get_text(content)
        for match in url_pattern.findall(text):
            cleaned = match.rstrip(".,;\"')]>")
            if cleaned not in urls:
                urls.append(cleaned)

        # Check tool calls parameters
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                args = tc.get("args", {})
                for v in args.values():
                    if isinstance(v, str):
                        for match in url_pattern.findall(v):
                            cleaned = match.rstrip(".,;\"')]>")
                            if cleaned not in urls:
                                urls.append(cleaned)
    return urls


def _extract_scraped_url(messages, fallback_urls: list[str] = None) -> str:
    """Find the specific URL passed to scrape_url tool call."""
    for msg in messages:
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                if tc.get("name") == "scrape_url":
                    url = tc.get("args", {}).get("url")
                    if url:
                        return url.strip()

    # Fallback to any URL found in reader agent messages
    urls = _extract_all_urls(messages)
    if urls:
        return urls[0]

    # Fallback to the first available URL from search
    if fallback_urls and len(fallback_urls) > 0:
        return fallback_urls[0]

    return "https://en.wikipedia.org"


def run_research_pipeline(topic: str, on_step_callback=None) -> dict:
    """
    Execute the multi-agent research pipeline.

    Args:
        topic (str): The research topic.
        on_step_callback (callable, optional): Callback function invoked after each step:
            callback(step_id: str, content: str, **kwargs)

    Returns:
        dict: The final pipeline state containing all agent outputs and URLs.
    """
    state = {}
    
    # -------------------------------------------------------------------------
    # Step 1: Search Agent
    # -------------------------------------------------------------------------
    print("\n" + " = " * 50, flush=True)
    print("Step 1 - Search agent is working...!", flush=True)
    print("=" * 50, flush=True)

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [("user", f"find recent, detailed and reliable information about {topic}. Make sure to include relevant source URLs.")]
    })

    search_messages = search_result.get("messages", [])
    state["search_results"] = _get_text(search_messages[-1].content)
    
    # Extract all discovered URLs from Tavily results
    state["tavily_urls"] = _extract_all_urls(search_messages)

    print("\nsearch result:\n", state["search_results"], flush=True)
    print("\nDiscovered Tavily URLs:\n", state["tavily_urls"], flush=True)

    if on_step_callback:
        on_step_callback("search", state["search_results"], urls=state["tavily_urls"])

    # -------------------------------------------------------------------------
    # Step 2: Reader Agent
    # -------------------------------------------------------------------------
    print("\n" + " = " * 50, flush=True)
    print("Step 2 - Reader agent is working...!", flush=True)
    print("=" * 50, flush=True)

    # Provide URLs explicitly to reader agent
    urls_prompt = "\n".join([f"- {u}" for u in state["tavily_urls"][:5]])
    reader_prompt = (
        f"Based on the following search results about {topic}, pick the most authoritative and informative URL "
        f"from the list and use scrape_url to fetch its full content.\n\n"
        f"Available URLs:\n{urls_prompt}\n\n"
        f"Search Summary:\n{state['search_results'][:800]}"
    )

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user", reader_prompt)]
    })

    reader_messages = reader_result.get("messages", [])
    state["scraped_content"] = _get_text(reader_messages[-1].content)
    state["scraped_url"] = _extract_scraped_url(reader_messages, fallback_urls=state["tavily_urls"])

    print("\nScraped URL:\n", state["scraped_url"], flush=True)
    print("\nScraped content:\n", state["scraped_content"][:300] + "...", flush=True)

    if on_step_callback:
        on_step_callback("reader", state["scraped_content"], scraped_url=state["scraped_url"])

    # -------------------------------------------------------------------------
    # Step 3: Writer Agent
    # -------------------------------------------------------------------------
    print("\n" + " = " * 50, flush=True)
    print("Step 3 - Writer agent is working...!", flush=True)
    print("=" * 50, flush=True)

    # Compile structured research package with explicit URLs
    tavily_sources_str = "\n".join([f"- {u}" for u in state["tavily_urls"]]) if state["tavily_urls"] else "None found"
    research_combined = (
        f"--- GATHERED SOURCE URLS (FROM TAVILY SEARCH) ---\n"
        f"{tavily_sources_str}\n\n"
        f"--- PRIMARY DEEP-SCRAPED SOURCE URL ---\n"
        f"{state['scraped_url']}\n\n"
        f"--- SEARCH INTELLIGENCE SUMMARY ---\n"
        f"{state['search_results']}\n\n"
        f"--- IN-DEPTH SCRAPED WEBPAGE CONTENT ---\n"
        f"{state['scraped_content']}"
    )

    state["report"] = _get_text(writer_chain.invoke({
        "topic": topic,        
        "research": research_combined
    }))    
    
    print("\n" + " = " * 50, flush=True)
    print("\nfinal report:\n", state["report"], flush=True)

    if on_step_callback:
        on_step_callback("writer", state["report"])

    # -------------------------------------------------------------------------
    # Step 4: Critic Agent
    # -------------------------------------------------------------------------
    print("\n" + " = " * 50, flush=True)
    print("Step 4 - Critic agent is working...!", flush=True)
    print("=" * 50, flush=True)

    state["feedback"] = _get_text(critic_chain.invoke({
        "report": state["report"]
    }))    
    
    print("\n" + " = " * 50, flush=True)
    print("\nCritic report:\n", state["feedback"], flush=True)

    if on_step_callback:
        on_step_callback("critic", state["feedback"])

    return state
