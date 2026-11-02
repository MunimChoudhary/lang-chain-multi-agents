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
    page_title="Multi-Agent AI Research Studio",
    page_icon="🔬",
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
# Sidebar: Setup, Agents Overview, & Templates
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🔬 Multi-Agent Studio")
    st.caption("Orchestrated research pipeline powered by LangChain & Google Gemini")
    st.divider()

    # Environment Status
    st.markdown("#### 🔑 System Status")
    google_key = os.getenv("GOOGLE_API_KEY", "")
    tavily_key = os.getenv("TAVILY_API_KEY", "")

    col_g, col_t = st.columns(2)
    with col_g:
        if google_key:
            st.success("Google AI\nReady", icon="🟢")
        else:
            st.error("Google AI\nMissing", icon="🔴")

    with col_t:
        if tavily_key:
            st.success("Tavily\nReady", icon="🟢")
        else:
            st.error("Tavily\nMissing", icon="🔴")

    # API Key Override Expander
    with st.expander("⚙️ Configure API Keys"):
        new_g_key = st.text_input("GOOGLE_API_KEY", value=google_key, type="password")
        new_t_key = st.text_input("TAVILY_API_KEY", value=tavily_key, type="password")
        if st.button("Save Keys", use_container_width=True):
            if new_g_key:
                os.environ["GOOGLE_API_KEY"] = new_g_key
            if new_t_key:
                os.environ["TAVILY_API_KEY"] = new_t_key
            st.success("API Keys updated in runtime!")
            st.rerun()

    st.divider()

    # Agent Architecture
    st.markdown("#### 🤖 Agent Architecture")
    st.markdown(
        """
        <div class="agent-card">
            <div class="agent-title">🔍 1. Search Agent</div>
            <div class="agent-desc">Queries Tavily for fresh, reliable search snippets and source links.</div>
        </div>
        <div class="agent-card">
            <div class="agent-title">📖 2. Reader Agent</div>
            <div class="agent-desc">Scrapes and extracts full article text using Trafilatura & Readability.</div>
        </div>
        <div class="agent-card">
            <div class="agent-title">✍️ 3. Writer Agent</div>
            <div class="agent-desc">Synthesizes findings into a professional, structured research report.</div>
        </div>
        <div class="agent-card">
            <div class="agent-title">🧐 4. Critic Agent</div>
            <div class="agent-desc">Peer-reviews content, scores depth, and points out gaps.</div>
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
st.markdown('<div class="hero-title">🔬 Autonomous Research Multi-Agent Team</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-subtitle">Enter any research inquiry to dispatch a coordinated team of autonomous agents to search, read, synthesize, and peer-critique a complete dossier.</div>',
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
        st.error("Missing Google API Key. Please configure it in the sidebar or in your .env file.")
    elif not os.getenv("TAVILY_API_KEY"):
        st.error("Missing Tavily API Key. Please configure it in the sidebar or in your .env file.")
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

        step_placeholders["search"].markdown("⏳ **Step 1:** Search Agent is querying the web...")
        start_time = time.time()

        def on_step_update(step_id: str, content: str):
            if step_id == "search":
                step_placeholders["search"].markdown("✅ **Step 1:** Search Agent gathered live intelligence!")
                step_placeholders["reader"].markdown("⏳ **Step 2:** Reader Agent is selecting and scraping URLs...")
            elif step_id == "reader":
                step_placeholders["reader"].markdown("✅ **Step 2:** Reader Agent extracted deep article content!")
                step_placeholders["writer"].markdown("⏳ **Step 3:** Writer Agent is synthesizing research report...")
            elif step_id == "writer":
                step_placeholders["writer"].markdown("✅ **Step 3:** Writer Agent produced structured report!")
                step_placeholders["critic"].markdown("⏳ **Step 4:** Critic Agent is auditing and scoring...")
            elif step_id == "critic":
                step_placeholders["critic"].markdown("✅ **Step 4:** Critic Agent finalized peer evaluation!")

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
                <div class="metric-value">{critic_score}</div>
                <div class="metric-label">Critic Score</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-value">4 / 4</div>
                <div class="metric-label">Agents Coordinated</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Tabs for Outputs
    tab_report, tab_critic, tab_search, tab_scraped = st.tabs(
        [
            "📑 Final Research Report",
            "🧐 Critic Review & Audit",
            "🔍 Search Agent Intel",
            "📖 Reader Agent Scrape",
        ]
    )

    # 1. Final Report Tab
    with tab_report:
        st.subheader("📑 Synthesized Research Report")
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

    # 2. Critic Review Tab
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

    # 3. Search Intel Tab
    with tab_search:
        st.subheader("🔍 Search Agent Findings")
        st.caption("Live web queries and snippets returned by the Tavily search engine.")
        st.text_area(
            "Raw Search Agent Output",
            value=search_text,
            height=400,
            disabled=True,
        )

    # 4. Reader Agent Tab
    with tab_scraped:
        st.subheader("📖 Reader Agent Extracted Content")
        st.caption("Main article text scraped and parsed from the most relevant source.")
        st.text_area(
            "Extracted Web Content",
            value=scraped_text,
            height=400,
            disabled=True,
        )
