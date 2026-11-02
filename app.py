import time
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.pipelines.pipelines import run_research_pipeline

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="DeepSearch — Autonomous AI Research",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Custom Styling
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Global Container Adjustments */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    /* Hero Header */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1E88E5 0%, #7B1FA2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #666;
        margin-bottom: 1.5rem;
    }

    /* Metric Cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E88E5;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* Agent Role Badges in Sidebar */
    .agent-card {
        padding: 0.75rem;
        margin-bottom: 0.6rem;
        border-radius: 8px;
        border-left: 4px solid #1E88E5;
        background: rgba(30, 136, 229, 0.08);
    }
    .agent-title {
        font-weight: 700;
        font-size: 0.95rem;
    }
    .agent-desc {
        font-size: 0.8rem;
        color: #777;
    }

    /* URL Citation Card */
    .sources-box {
        background: rgba(30, 136, 229, 0.05);
        border: 1px solid rgba(30, 136, 229, 0.2);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }
    .source-tag {
        display: inline-block;
        background: rgba(30, 136, 229, 0.12);
        color: #1E88E5;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.85rem;
        margin: 3px 4px;
        text-decoration: none;
    }
    .source-tag:hover {
        background: rgba(30, 136, 229, 0.25);
    }

    /* Critic Evaluation Card */
    .critic-card {
        border-left: 4px solid #E53935;
        background: rgba(229, 57, 53, 0.05);
        border-radius: 8px;
        padding: 1rem;
        margin-top: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Initialize Session State
# -----------------------------------------------------------------------------
if "pipeline_results" not in st.session_state:
    st.session_state.pipeline_results = None

if "research_topic" not in st.session_state:
    st.session_state.research_topic = "Advancements in Autonomous AI Agents and Multi-Agent Systems"

if "execution_time" not in st.session_state:
    st.session_state.execution_time = 0


# Helper to preset topic from suggestions
def select_topic(topic_text: str):
    st.session_state.research_topic = topic_text


# Helper to parse critic score
def extract_critic_score(feedback_text: str) -> str:
    if not feedback_text:
        return "N/A"
    for line in feedback_text.splitlines():
        if "score" in line.lower() and ":" in line:
            parts = line.split(":", 1)
            return parts[1].strip()
    return "Reviewed"


# -----------------------------------------------------------------------------
# Sidebar: Setup, Agents Overview, & Templates (NO API KEYS EXPOSED)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔍 DeepSearch")
    st.caption("Autonomous multi-agent research powered by LangChain & Google Gemini")
    st.divider()

    # System Status (Privacy-preserving: never display API keys)
    st.markdown("#### 🛡️ System Status")
    google_configured = bool(os.getenv("GOOGLE_API_KEY"))
    tavily_configured = bool(os.getenv("TAVILY_API_KEY"))

    col_g, col_t = st.columns(2)
    with col_g:
        if google_configured:
            st.success("Google AI\nReady", icon="🟢")
        else:
            st.error("Google AI\nMissing", icon="🔴")

    with col_t:
        if tavily_configured:
            st.success("Tavily\nReady", icon="🟢")
        else:
            st.error("Tavily\nMissing", icon="🔴")

    if not (google_configured and tavily_configured):
        st.warning("⚠️ Ensure GOOGLE_API_KEY and TAVILY_API_KEY are configured in your `.env` file.")

    st.divider()

    # Agent Architecture
    st.markdown("#### 🤖 Agent Architecture")
    st.markdown(
        """
        <div class="agent-card">
            <div class="agent-title">🔍 1. Search Agent</div>
            <div class="agent-desc">Queries Tavily for live sources & URLs.</div>
        </div>
        <div class="agent-card">
            <div class="agent-title">📖 2. Reader Agent</div>
            <div class="agent-desc">Scrapes deep content from the most relevant URL.</div>
        </div>
        <div class="agent-card">
            <div class="agent-title">✍️ 3. Writer Agent</div>
            <div class="agent-desc">Synthesizes report and cites all discovered URLs.</div>
        </div>
        <div class="agent-card">
            <div class="agent-title">🧐 4. Critic Agent</div>
            <div class="agent-desc">Audits factual depth, citations, and scores quality.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # Quick Suggestion Templates
    st.markdown("#### 💡 Quick Topics")
    suggestions = [
        "Advancements in Autonomous AI Agents",
        "Next-Gen Nuclear Fusion Energy Breakthroughs",
        "Space Exploration and Artemis Moon Missions",
        "Quantum Computing Roadmap and Real-World Use",
    ]
    for sug in suggestions:
        st.button(
            sug,
            key=f"btn_{sug}",
            use_container_width=True,
            on_click=select_topic,
            args=(sug,),
        )

# -----------------------------------------------------------------------------
# Main Interface
# -----------------------------------------------------------------------------
st.markdown('<div class="hero-title">🔍 DeepSearch</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Autonomous Multi-Agent Research System — Discover sources, scrape in-depth content, synthesize reports, and peer-review findings.</div>',
    unsafe_allow_html=True,
)

# Research Input Bar
with st.container():
    topic_input = st.text_input(
        "Enter your research topic or question:",
        value=st.session_state.research_topic,
        placeholder="e.g. Current trends in renewable energy storage...",
        label_visibility="collapsed",
    )

    col1, col2, col3 = st.columns([2, 1, 3])
    with col1:
        run_button = st.button("🚀 Dispatch Agents", type="primary", use_container_width=True)
    with col2:
        if st.session_state.pipeline_results is not None:
            if st.button("🧹 Clear Results", use_container_width=True):
                st.session_state.pipeline_results = None
                st.rerun()

# -----------------------------------------------------------------------------
# Execution Flow with Live Updates
# -----------------------------------------------------------------------------
if run_button:
    if not topic_input.strip():
        st.warning("Please enter a research topic to begin.")
    elif not os.getenv("GOOGLE_API_KEY"):
        st.error("Missing GOOGLE_API_KEY in .env file.")
    elif not os.getenv("TAVILY_API_KEY"):
        st.error("Missing TAVILY_API_KEY in .env file.")
    else:
        st.session_state.research_topic = topic_input.strip()

        # Visual progress container
        progress_box = st.status("🚀 Initializing autonomous agents...", expanded=True)
        step_placeholders = {
            "search": progress_box.empty(),
            "reader": progress_box.empty(),
            "writer": progress_box.empty(),
            "critic": progress_box.empty(),
        }

        step_placeholders["search"].markdown("⏳ **Step 1:** Search Agent is querying Tavily for web sources & URLs...")
        start_time = time.time()

        def on_step_update(step_id: str, content: str, **kwargs):
            if step_id == "search":
                urls_found = kwargs.get("urls", [])
                count = len(urls_found)
                step_placeholders["search"].markdown(f"✅ **Step 1:** Search Agent discovered **{count} source URLs**!")
                step_placeholders["reader"].markdown("⏳ **Step 2:** Reader Agent is selecting and scraping the best URL...")
            elif step_id == "reader":
                scraped_url = kwargs.get("scraped_url", "Webpage")
                step_placeholders["reader"].markdown(f"✅ **Step 2:** Reader Agent scraped content from `{scraped_url}`!")
                step_placeholders["writer"].markdown("⏳ **Step 3:** Writer Agent is synthesizing report with citations...")
            elif step_id == "writer":
                step_placeholders["writer"].markdown("✅ **Step 3:** Writer Agent completed report with reference URLs!")
                step_placeholders["critic"].markdown("⏳ **Step 4:** Critic Agent is reviewing and scoring...")
            elif step_id == "critic":
                step_placeholders["critic"].markdown("✅ **Step 4:** Critic Agent completed evaluation!")

        try:
            results = run_research_pipeline(
                topic=topic_input.strip(),
                on_step_callback=on_step_update,
            )
            elapsed = time.time() - start_time
            st.session_state.execution_time = elapsed
            st.session_state.pipeline_results = results
            progress_box.update(
                label=f"🎉 Research Pipeline Completed in {elapsed:.1f}s!",
                state="complete",
                expanded=False,
            )
            st.rerun()

        except Exception as e:
            progress_box.update(label="❌ Pipeline Failed", state="error", expanded=True)
            st.error(f"Error during execution: {str(e)}")

# -----------------------------------------------------------------------------
# Results Presentation
# -----------------------------------------------------------------------------
if st.session_state.pipeline_results:
    results = st.session_state.pipeline_results
    report_text = results.get("report", "")
    critic_text = results.get("feedback", "")
    search_text = results.get("search_results", "")
    scraped_text = results.get("scraped_content", "")
    tavily_urls = results.get("tavily_urls", [])
    scraped_url = results.get("scraped_url", "")

    # Top Metrics Bar
    word_count = len(report_text.split()) if report_text else 0
    critic_score = extract_critic_score(critic_text)

    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{st.session_state.execution_time:.1f}s</div>
                <div class="metric-label">Pipeline Duration</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{word_count}</div>
                <div class="metric-label">Report Word Count</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{len(tavily_urls)}</div>
                <div class="metric-label">URLs Discovered</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{critic_score}</div>
                <div class="metric-label">Critic Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Tabs for Outputs
    tab_report, tab_sources, tab_critic, tab_search, tab_scraped = st.tabs(
        [
            "📑 Final Research Report",
            "🔗 Source URLs & Provenance",
            "🧐 Critic Review & Audit",
            "🔍 Search Agent Intel",
            "📖 Reader Agent Scrape",
        ]
    )

    # -------------------------------------------------------------------------
    # 1. Final Report Tab
    # -------------------------------------------------------------------------
    with tab_report:
        st.subheader("📑 Synthesized Research Report")

        # Sources summary banner at top of report
        if scraped_url:
            st.info(f"📍 **Deep-Scraped Primary Source:** [{scraped_url}]({scraped_url})")

        col_down, _ = st.columns([1, 4])
        with col_down:
            st.download_button(
                label="📥 Download Report (.md)",
                data=report_text,
                file_name=f"research_report_{int(time.time())}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        st.markdown(report_text)

    # -------------------------------------------------------------------------
    # 2. Source URLs & Provenance Tab
    # -------------------------------------------------------------------------
    with tab_sources:
        st.subheader("🔗 Discovered & Scraped Source URLs")
        st.caption("Complete breakdown of the URLs retrieved by Tavily and the primary page scraped by the Reader Agent.")

        # Deep-Scraped Source Card
        st.markdown("#### 🎯 Primary Deep-Scraped Source")
        if scraped_url and scraped_url != "N/A":
            st.markdown(
                f"""
                <div style="background: rgba(30,136,229,0.08); border-left: 4px solid #1E88E5; padding: 12px; border-radius: 6px; margin-bottom: 1.5rem;">
                    <strong>Scraped URL:</strong> <a href="{scraped_url}" target="_blank" style="color: #1E88E5; word-break: break-all;">{scraped_url}</a>
                    <br><small style="color: #888;">This webpage was selected by the Reader Agent for in-depth content extraction via Trafilatura.</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.write("No specific URL scraped.")

        # Tavily Discovered URLs
        st.markdown(f"#### 🌐 All URLs Discovered by Tavily Search ({len(tavily_urls)})")
        if tavily_urls:
            for idx, url in enumerate(tavily_urls, 1):
                col_num, col_link = st.columns([1, 15])
                with col_num:
                    st.markdown(f"**{idx}.**")
                with col_link:
                    st.markdown(f"[{url}]({url})")
        else:
            st.write("No external URLs returned.")

    # -------------------------------------------------------------------------
    # 3. Critic Review Tab
    # -------------------------------------------------------------------------
    with tab_critic:
        st.subheader("🧐 Peer Critique & Quality Assessment")
        st.caption(
            "The Critic Agent independently examines the synthesized report against standards for factual grounding, "
            "depth, balance, and citations."
        )
        st.markdown(
            """
            <div class="critic-card">
                <h4>🛡️ Peer Review Evaluation</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(critic_text)

    # -------------------------------------------------------------------------
    # 4. Search Intel Tab
    # -------------------------------------------------------------------------
    with tab_search:
        st.subheader("🔍 Search Agent Findings")
        st.caption("Live web queries and snippets returned by the Tavily search engine.")
        if tavily_urls:
            st.markdown("**Discovered URLs:**")
            for u in tavily_urls:
                st.markdown(f"- [{u}]({u})")
            st.divider()

        st.text_area(
            "Raw Search Agent Output",
            value=search_text,
            height=400,
            disabled=True,
        )

    # -------------------------------------------------------------------------
    # 5. Reader Agent Tab
    # -------------------------------------------------------------------------
    with tab_scraped:
        st.subheader("📖 Reader Agent Extracted Content")
        if scraped_url:
            st.info(f"Target Scraped URL: [{scraped_url}]({scraped_url})")

        st.text_area(
            "Extracted Web Content",
            value=scraped_text,
            height=400,
            disabled=True,
        )
