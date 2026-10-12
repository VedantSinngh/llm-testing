"""PromptLab Main Dashboard & System Overview.

This is the landing page for the Streamlit multipage application. It displays
system status, operational metrics, architecture diagrams, and quick navigations.
"""

import streamlit as st

from promptlab.dashboard.api_client import PromptLabClient

st.set_page_config(
    page_title="PromptLab - LLM Evaluation & Guardrails Playground",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom sleek CSS styling for high-end UI aesthetics
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #f8fafc;
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 4px;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-online {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }
    .status-offline {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(248, 113, 113, 0.3);
    }
    .feature-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 12px;
        padding: 20px;
        height: 100%;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .feature-card:hover {
        border-color: rgba(99, 102, 241, 0.5);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_client() -> PromptLabClient:
    """Retrieve cached PromptLabClient instance."""
    if "client" not in st.session_state:
        st.session_state.client = PromptLabClient()
    return st.session_state.client  # type: ignore[no-any-return]


client = get_client()
health = client.health()
is_connected = health.get("status") == "ok"

# Header section
st.markdown('<div class="main-title">🧪 PromptLab</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Product-Grade LLM Evaluation & Guardrails Playground</div>',
    unsafe_allow_html=True,
)

# System health and status bar
col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

with col_stat1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-title">Backend Status</div>', unsafe_allow_html=True)
    if is_connected:
        st.markdown(
            '<div class="status-badge status-online">● API Connected</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-badge status-offline">○ Offline / Demo</div>',
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

with col_stat2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-title">Inference Provider</div>', unsafe_allow_html=True)
    provider_name = health.get("active_provider", "offline").upper()
    st.markdown(f'<div class="metric-value">{provider_name}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_stat3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-title">Demo Mode</div>', unsafe_allow_html=True)
    demo_status = "ENABLED (Mock)" if health.get("demo_mode", True) else "DISABLED (Live Groq)"
    st.markdown(f'<div class="metric-value" style="font-size: 1.3rem;">{demo_status}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col_stat4:
    # Query total suites count if reachable
    total_suites = 0
    if is_connected:
        try:
            suites_data = client.list_suites(limit=1)
            total_suites = suites_data.get("total", 0)
        except Exception:
            total_suites = 0
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown('<div class="metric-title">Registered Suites</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{total_suites}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# Module Navigation Showcase
st.subheader("Explore Modules")

col_m1, col_m2 = st.columns(2)

with col_m1:
    st.markdown(
        """
        <div class="feature-card">
            <h3>🎯 1. Interactive Playground</h3>
            <p style="color: #cbd5e1;">
                Experiment in real-time with prompt engineering strategies (Zero-Shot, Few-Shot,
                Chain-of-Thought, Structured Output). Adjust sampling temperature and compare outputs
                with instant rubric scoring.
            </p>
            <p style="color: #818cf8; font-weight: 600;">Go to sidebar → 1_Playground</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        """
        <div class="feature-card">
            <h3>🛡️ 3. Safety & Guardrails</h3>
            <p style="color: #cbd5e1;">
                Execute adversarial prompt injection test suites (Direct overrides, roleplay jailbreaks,
                encoded vectors) with canary token leak detection. Scan text payloads for PII, emails,
                phone numbers, and API keys with real-time redaction.
            </p>
            <p style="color: #818cf8; font-weight: 600;">Go to sidebar → 3_Safety_&_Guardrails</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_m2:
    st.markdown(
        """
        <div class="feature-card">
            <h3>📋 2. Evaluation Suites</h3>
            <p style="color: #cbd5e1;">
                Build reusable test suites with deterministic scorers (Exact Match, Regex, JSON Schema,
                SQL Execution, LLM Judge). Execute concurrency-managed batch runs across open-source models
                (Llama 3.3, Qwen 2.5, Mistral Large, Gemma 2).
            </p>
            <p style="color: #818cf8; font-weight: 600;">Go to sidebar → 2_Test_Suites</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.markdown(
        """
        <div class="feature-card">
            <h3>📊 4. History & Comparison</h3>
            <p style="color: #cbd5e1;">
                Compare evaluation runs side-by-side with matrix alignments, leaderboards for latency,
                pass rates, and token costs. Audit historical safety evaluations and export metrics.
            </p>
            <p style="color: #818cf8; font-weight: 600;">Go to sidebar → 4_History_&_Comparison</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# Architecture & Interview Explanation Callout
with st.expander("🎓 Architecture & Interview Design Highlights (How to explain PromptLab)", expanded=False):
    st.markdown(
        """
        - **Decoupled Architecture:** Pure domain core (`core/`) contains zero framework dependencies.
          FastAPI (`api/`) and Streamlit (`dashboard/`) communicate strictly through standardized REST DTOs.
        - **Design Patterns in Practice:**
          - **Template Method:** BaseScorer (`_preprocess` → `_evaluate` → `_finalize`) for uniform metric calculation.
          - **Strategy Pattern:** PromptTechnique hierarchy for swappable prompt engineering formulations.
          - **Factory & Registry:** ProviderFactory allows adding inference providers (OpenAI, Anthropic, vLLM) with zero code modifications.
          - **Facade Pattern:** EvaluationService simplifies complex orchestration of test runners, repositories, and providers.
          - **Repository Pattern:** Database persistence decoupled from business logic via typed async SQLAlchemy 2.0 repositories.
        - **Reliability & Safety:**
          - Exponential backoff jitter retries on 429/5xx status codes.
          - Defense-in-depth SQL query validation strictly blocking non-SELECT queries.
          - High-entropy canary token tracking detecting model boundary breaches.
        """
    )
