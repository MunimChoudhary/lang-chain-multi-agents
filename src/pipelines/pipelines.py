import sys
import re

# Ensure Windows terminal handles UTF-8 characters without charmap errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.agents.agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
from src.tools.tools import web_search, scrape_url


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


def _extract_all_urls(data) -> list[str]:
    """Extract unique HTTP/HTTPS URLs from messages, tool calls, or text strings."""
    urls = []
    url_pattern = re.compile(r"https?://[^\s\)\"\'\<\>]+", re.IGNORECASE)

    if isinstance(data, str):
        for match in url_pattern.findall(data):
            cleaned = match.rstrip(".,;\"')]>")
            if cleaned not in urls:
                urls.append(cleaned)
        return urls

    if isinstance(data, list):
        for msg in data:
            if isinstance(msg, str):
                for match in url_pattern.findall(msg):
                    cleaned = match.rstrip(".,;\"')]>")
                    if cleaned not in urls:
                        urls.append(cleaned)
            else:
                content = getattr(msg, "content", "")
                text = _get_text(content)
                for match in url_pattern.findall(text):
                    cleaned = match.rstrip(".,;\"')]>")
                    if cleaned not in urls:
                        urls.append(cleaned)

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


def run_research_pipeline(topic: str, on_step_callback=None) -> dict:
    """
    Execute the multi-agent research pipeline with guaranteed URL discovery and scraping.

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
    search_prompt = (
        f"Search the web using the web_search tool for comprehensive, reliable, and up-to-date "
        f"information about {topic}. You MUST use the web_search tool to find real web results and URLs."
    )
    search_result = search_agent.invoke({"messages": [("user", search_prompt)]})

    search_messages = search_result.get("messages", [])
    agent_output = _get_text(search_messages[-1].content) if search_messages else ""
    tavily_urls = _extract_all_urls(search_messages)

    # GUARANTEE: If LLM didn't invoke the search tool or returned no URLs, invoke Tavily directly
    if not tavily_urls or len(tavily_urls) == 0:
        print("Ensuring live Tavily URLs via direct tool query...", flush=True)
        raw_tavily = web_search.invoke({"query": topic})
        tavily_urls = _extract_all_urls(raw_tavily)
        agent_output = f"{agent_output}\n\n### Discovered Sources & Search Results:\n{raw_tavily}"

    state["search_results"] = agent_output
    state["tavily_urls"] = tavily_urls

    print(f"\nDiscovered Tavily URLs ({len(tavily_urls)}):", flush=True)
    for u in tavily_urls:
        print(f"  - {u}", flush=True)

    if on_step_callback:
        on_step_callback("search", state["search_results"], urls=state["tavily_urls"])

    # -------------------------------------------------------------------------
    # Step 2: Reader Agent
    # -------------------------------------------------------------------------
    print("\n" + " = " * 50, flush=True)
    print("Step 2 - Reader agent is working...!", flush=True)
    print("=" * 50, flush=True)

    # Pick the most authoritative non-video URL to scrape
    target_url = None
    for u in state["tavily_urls"]:
        if "youtube.com" not in u and "youtu.be" not in u:
            target_url = u
            break
    if not target_url and state["tavily_urls"]:
        target_url = state["tavily_urls"][0]
    if not target_url:
        target_url = f"https://en.wikipedia.org/wiki/{topic.strip().replace(' ', '_')}"

    reader_prompt = (
        f"You are the Reader Agent. You MUST use the scrape_url tool on this exact URL:\n"
        f"{target_url}\n"
        f"Scrape its webpage content and provide a detailed analysis of what you read."
    )

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({"messages": [("user", reader_prompt)]})

    reader_messages = reader_result.get("messages", [])
    scraped_content = ""

    # Look for ToolMessage content
    for msg in reader_messages:
        if type(msg).__name__ == "ToolMessage" or getattr(msg, "name", "") == "scrape_url":
            scraped_content = _get_text(msg.content)
            break

    # If ToolMessage was empty or short, fallback to last agent message or direct scrape
    if not scraped_content or len(scraped_content.strip()) < 100:
        if reader_messages:
            scraped_content = _get_text(reader_messages[-1].content)
        if not scraped_content or len(scraped_content.strip()) < 100:
            print(f"Scraping {target_url} directly to guarantee full text...", flush=True)
            scraped_content = scrape_url.invoke({"url": target_url})

    state["scraped_url"] = target_url
    state["scraped_content"] = scraped_content

    print(f"\nScraped URL: {state['scraped_url']}", flush=True)
    print(f"Scraped content length: {len(state['scraped_content'])} characters", flush=True)

    if on_step_callback:
        on_step_callback("reader", state["scraped_content"], scraped_url=state["scraped_url"])

    # -------------------------------------------------------------------------
    # Step 3: Writer Agent
    # -------------------------------------------------------------------------
    print("\n" + " = " * 50, flush=True)
    print("Step 3 - Writer agent is working...!", flush=True)
    print("=" * 50, flush=True)

    # Compile structured research package with explicit URLs
    sources_list = "\n".join([f"{idx}. {u}" for idx, u in enumerate(state["tavily_urls"], 1)])
    research_combined = (
        f"===================================================================\n"
        f"MANDATORY REFERENCE URLS (YOU MUST CITE THESE IN THE FINAL REPORT):\n"
        f"Primary Deep-Scraped Source URL: {state['scraped_url']}\n\n"
        f"All Discovered Reference URLs:\n{sources_list}\n"
        f"===================================================================\n\n"
        f"--- GATHERED SEARCH INTELLIGENCE ---\n{state['search_results']}\n\n"
        f"--- IN-DEPTH SCRAPED WEBPAGE CONTENT (FROM {state['scraped_url']}) ---\n{state['scraped_content'][:10000]}"
    )

    state["report"] = _get_text(writer_chain.invoke({
        "topic": topic,
        "research": research_combined
    }))

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

    print("\nCritic report:\n", state["feedback"], flush=True)

    if on_step_callback:
        on_step_callback("critic", state["feedback"])

    return state
