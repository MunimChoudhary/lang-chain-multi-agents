import sys

# Ensure Windows terminal handles UTF-8 characters without charmap errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.tools.tools import web_search, scrape_url
from src.pipelines.pipelines import run_research_pipeline

result = run_research_pipeline("Tell me something about Pakistan?")
