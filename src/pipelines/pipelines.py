import sys

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


def run_research_pipeline(topic: str) -> dict:

    state = {}
    
    # Step 1: Search agent
    print("\n" + " = " * 50, flush=True)
    print("Step 1 - Search agent is working...!", flush=True)
    print("=" * 50, flush=True)

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [("user", f"find recent, detailed and reliable information about {topic}")]
    })

    state["search_results"] = _get_text(search_result["messages"][-1].content)
    print("\nsearch result:\n", state["search_results"], flush=True)

    # Step 2: Reader agent
    print("\n" + " = " * 50, flush=True)
    print("Step 2 - Reader agent is working...!", flush=True)
    print("=" * 50, flush=True)

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user", 
            f"based on the following search result about {topic}, "
            f"pick the most relevant url and scrape it for deeper content. \n\n"
            f"search results: \n{state['search_results'][:800]}"
        )]
    })

    state["scraped_content"] = _get_text(reader_result["messages"][-1].content)
    print("\nscraped content:\n", state["scraped_content"], flush=True)

    # Step 3: Writer agent
    print("\n" + " = " * 50, flush=True)
    print("Step 3 - Writer agent is working...!", flush=True)
    print("=" * 50, flush=True)

    research_combined = (
        f"search results: \n{state['search_results']}\n\n"
        f"detailed scraped content:\n{state['scraped_content']}"
    )

    state["report"] = _get_text(writer_chain.invoke({
        "topic": topic,        
        "research": research_combined
    }))    
    
    print("\n" + " = " * 50, flush=True)
    print("\nfinal report:\n", state["report"], flush=True)

    # Step 4: Critic agent
    print("\n" + " = " * 50, flush=True)
    print("Step 4 - Critic agent is working...!", flush=True)
    print("=" * 50, flush=True)

    state["feedback"] = _get_text(critic_chain.invoke({
        "report": state["report"]
    }))    
    
    print("\n" + " = " * 50, flush=True)
    print("\nCritic report:\n", state["feedback"], flush=True)

    return state
