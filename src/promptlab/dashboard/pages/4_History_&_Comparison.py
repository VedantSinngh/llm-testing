"""Historical Evaluation Runs Explorer and Side-by-Side Comparative Analytics.

This page provides:
- Side-by-side run comparisons across models and prompt techniques.
- Leaderboard metrics highlighting top pass rates and lowest latencies.
- Granular per-case comparison matrices.
- Historical run browsing and inspection.
"""

from typing import Any

import streamlit as st

from promptlab.dashboard.api_client import PromptLabClient

st.set_page_config(page_title="History & Comparison - PromptLab", page_icon="📊", layout="wide")


def get_client() -> PromptLabClient:
    """Retrieve API client."""
    if "client" not in st.session_state:
        st.session_state.client = PromptLabClient()
    return st.session_state.client  # type: ignore[no-any-return]


client = get_client()

st.title("📊 Evaluation History & Comparative Analytics")
st.caption("Compare models, techniques, and parameter configurations side by side.")

tab_compare, tab_browse = st.tabs(["⚖️ Side-by-Side Comparison", "📜 Historical Run Explorer"])

# --- TAB 1: SIDE-BY-SIDE COMPARISON ---
with tab_compare:
    st.subheader("Compare Evaluation Runs")

    runs_data = client.list_runs(limit=100)
    all_runs = runs_data.get("items", [])

    if len(all_runs) < 2:
        st.info("At least 2 evaluation runs are required for side-by-side comparison. Execute runs in 'Playground' or 'Test Suites' first.")
    else:
        run_options = {
            f"[{r.get('model')}] Suite: {r.get('suite_name')} — Pass Rate: {r.get('pass_rate', 0)*100:.0f}% (ID: {r.get('run_id')[:8]}...)": r.get("run_id")
            for r in all_runs
        }

        selected_labels = st.multiselect(
            "Select 2 or more runs to compare:",
            options=list(run_options.keys()),
            default=list(run_options.keys())[:2] if len(run_options) >= 2 else [],
        )

        selected_ids = [run_options[lbl] for lbl in selected_labels]

        if len(selected_ids) >= 2:
            if st.button("🚀 Generate Comparison Analytics", type="primary"):
                with st.spinner("Calculating comparative metrics and aligning case matrices..."):
                    try:
                        comparison = client.compare_runs(selected_ids)

                        # Leaderboard Highlights
                        best_model = comparison.get("best_performing_model", "N/A")
                        fastest_model = comparison.get("fastest_model", "N/A")

                        col_lead1, col_lead2, col_lead3 = st.columns(3)
                        col_lead1.metric("Compared Runs", comparison.get("run_count", 0))
                        col_lead2.metric("🏆 Best Pass Rate", best_model)
                        col_lead3.metric("⚡ Fastest Model", fastest_model)

                        st.divider()

                        # Summaries Table
                        st.subheader("Run Summaries")
                        summaries = comparison.get("summaries", [])
                        st.dataframe(
                            [
                                {
                                    "Model": s.get("model"),
                                    "Suite": s.get("suite_name"),
                                    "Technique": s.get("technique"),
                                    "Pass Rate": f"{s.get('pass_rate', 0)*100:.1f}%",
                                    "Avg Latency (ms)": f"{s.get('avg_latency_ms', 0):.1f}",
                                    "Total Tokens": s.get("total_tokens", 0),
                                    "Temp": s.get("temperature"),
                                }
                                for s in summaries
                            ],
                            use_container_width=True,
                        )

                        st.divider()

                        # Per-Case Matrix
                        st.subheader("Per-Case Side-by-Side Matrix")
                        case_matrix = comparison.get("case_matrix", [])

                        for row in case_matrix:
                            cid = row.get("case_id", "")
                            with st.expander(f"Case ID: {cid}", expanded=False):
                                run_cols = st.columns(len(selected_ids))
                                for idx, rid in enumerate(selected_ids):
                                    run_info = row.get("runs", {}).get(rid)
                                    with run_cols[idx]:
                                        if run_info:
                                            m_name = run_info.get("model", "")
                                            score = run_info.get("score", 0.0)
                                            passed = run_info.get("passed", False)
                                            lat = run_info.get("latency_ms", 0.0)
                                            preview = run_info.get("output_preview", "")

                                            status_str = "✅ Passed" if passed else "❌ Failed"
                                            st.markdown(f"**{m_name}** ({status_str})")
                                            st.caption(f"Score: {score:.2f} | Latency: {lat:.1f}ms")
                                            st.text_area(
                                                "Output Preview",
                                                value=preview,
                                                height=80,
                                                key=f"prev_{cid}_{rid}",
                                                disabled=True,
                                            )
                                        else:
                                            st.caption("No result for this run.")

                    except Exception as exc:
                        st.error(f"Comparison failed: {exc}")
        else:
            st.warning("Please select at least 2 runs.")

# --- TAB 2: HISTORICAL RUN EXPLORER ---
with tab_browse:
    st.subheader("All Historical Runs")
    filter_model = st.text_input("Filter by Model Name (Optional)", value="")

    filtered_runs = all_runs
    if filter_model.strip():
        filtered_runs = [r for r in all_runs if filter_model.lower() in str(r.get("model", "")).lower()]

    if not filtered_runs:
        st.info("No matching runs found.")
    else:
        for r in filtered_runs:
            rid = r.get("run_id", "")
            sname = r.get("suite_name", "")
            rmodel = r.get("model", "")
            pass_rate = r.get("pass_rate", 0.0) * 100
            avg_lat = r.get("avg_latency_ms", 0.0)
            tokens = r.get("total_tokens", 0)

            with st.expander(f"[{rmodel}] {sname} — Pass Rate: {pass_rate:.1f}% — {avg_lat:.1f}ms (ID: {rid[:8]}...)"):
                st.write(f"Technique: `{r.get('technique')}` | Tokens: `{tokens}`")
                case_results = r.get("case_results", [])
                st.write(f"Evaluated Cases: {len(case_results)}")
                for cr in case_results:
                    cid = cr.get("case_id", "")
                    passed = cr.get("passed", False)
                    score = cr.get("score", 0.0)
                    resp = cr.get("response", {})
                    badge = "✅" if passed else "❌"
                    st.markdown(f"- {badge} **{cid}** (Score: {score:.2f}): `{resp.get('text', '')[:100]}...`")
