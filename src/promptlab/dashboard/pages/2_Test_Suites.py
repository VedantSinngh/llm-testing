"""Test Suites Management and Batch Evaluation Runner.

This page allows creating, inspecting, and running full evaluation test suites
with automated rubric scoring and aggregate metrics.
"""

import json
from typing import Any

import streamlit as st

from promptlab.dashboard.api_client import PromptLabClient

st.set_page_config(page_title="Test Suites - PromptLab", page_icon="📋", layout="wide")


def get_client() -> PromptLabClient:
    """Retrieve API client."""
    if "client" not in st.session_state:
        st.session_state.client = PromptLabClient()
    return st.session_state.client  # type: ignore[no-any-return]


client = get_client()

st.title("📋 Evaluation Test Suites")
st.caption("Manage test cases, run automated evaluations against LLMs, and track regressions.")

tab_run, tab_create, tab_manage = st.tabs(["🚀 Run Suite", "➕ Create Suite", "⚙️ Manage Existing Suites"])

# --- TAB 1: RUN SUITE ---
with tab_run:
    st.subheader("Execute Test Suite")

    # Fetch available suites
    suites_data = client.list_suites(limit=100)
    suite_items = suites_data.get("items", [])

    if not suite_items:
        st.info("No test suites found in the database. Create a suite in the 'Create Suite' tab or run a demo.")
    else:
        suite_map = {f"{s['suite']['name']} ({s['id'][:8]}...)": s for s in suite_items}
        selected_suite_label = st.selectbox("Select Test Suite", list(suite_map.keys()))
        selected_suite = suite_map[selected_suite_label]

        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
        with col_ctrl1:
            models = client.list_models()
            target_model = st.selectbox("Evaluation Model", models, index=0)
        with col_ctrl2:
            run_temp = st.slider("Temperature", 0.0, 2.0, 0.2, 0.05, key="run_temp")
        with col_ctrl3:
            run_tokens = st.slider("Max Tokens", 32, 2048, 256, 32, key="run_tokens")

        if st.button("🚀 Execute Suite Run", type="primary", use_container_width=True):
            with st.spinner(f"Evaluating {len(selected_suite['suite']['cases'])} cases on {target_model}..."):
                try:
                    run_payload = {
                        "suite_id": selected_suite["id"],
                        "model": target_model,
                        "params": {"temperature": run_temp, "max_tokens": run_tokens},
                    }
                    run_res = client.execute_run(run_payload)

                    st.success("Evaluation run completed!")

                    # Summary Metrics Bar
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    pass_rate = run_res.get("pass_rate", 0.0) * 100
                    col_m1.metric("Pass Rate", f"{pass_rate:.1f}%")
                    col_m2.metric("Avg Latency", f"{run_res.get('avg_latency_ms', 0):.1f} ms")
                    col_m3.metric("Total Tokens", run_res.get("total_tokens", 0))
                    col_m4.metric("Cases Evaluated", len(run_res.get("case_results", [])))

                    st.divider()

                    # Granular Case Results
                    st.subheader("Case Breakdown")
                    case_results = run_res.get("case_results", [])

                    for cr in case_results:
                        cid = cr.get("case_id", "")
                        passed = cr.get("passed", False)
                        score = cr.get("score", 0.0)
                        reason = cr.get("reason", "")
                        resp_obj = cr.get("response", {})
                        out_text = resp_obj.get("text", "")
                        lat = resp_obj.get("latency_ms", 0)

                        icon = "✅" if passed else "❌"
                        header = f"{icon} Case [{cid}] — Score: {score:.2f} ({'PASSED' if passed else 'FAILED'}) — {lat:.1f}ms"

                        with st.expander(header):
                            st.markdown(f"**Evaluation Reason:** {reason}")
                            st.markdown("**Model Output:**")
                            st.code(out_text, language="markdown")

                except Exception as exc:
                    st.error(f"Run execution failed: {exc}")

# --- TAB 2: CREATE SUITE ---
with tab_create:
    st.subheader("Create New Evaluation Suite")

    with st.form("create_suite_form"):
        suite_name = st.text_input("Suite Name", value="customer_service_eval")
        suite_desc = st.text_area("Description", value="Evaluation suite testing intent recognition and formatting.")
        suite_sys = st.text_input("System Prompt", value="You are a helpful customer service assistant.")
        suite_technique = st.selectbox("Prompt Technique", ["zero_shot", "few_shot", "chain_of_thought", "structured_output"])

        st.subheader("Test Cases (JSON format)")
        default_cases = [
            {
                "id": "case-01",
                "input": "Where is my order #1234?",
                "expected": "order",
                "scorer": "contains",
                "scorer_config": {"substring": "order"},
                "tags": ["tracking", "order"],
            },
            {
                "id": "case-02",
                "input": "What is 15 * 6?",
                "expected": "90",
                "scorer": "exact_match",
                "scorer_config": {"case_sensitive": False},
                "tags": ["math"],
            },
            {
                "id": "case-03",
                "input": "Write SQL to fetch active users from database.",
                "expected": None,
                "scorer": "sql_result",
                "scorer_config": {},
                "tags": ["database"],
            },
        ]
        cases_json_str = st.text_area(
            "Cases Definition",
            value=json.dumps(default_cases, indent=2),
            height=260,
        )

        submit_suite = st.form_submit_button("💾 Save Test Suite", type="primary")

    if submit_suite:
        try:
            parsed_cases = json.loads(cases_json_str)
            create_payload = {
                "name": suite_name.strip(),
                "description": suite_desc.strip(),
                "system_prompt": suite_sys.strip() if suite_sys.strip() else None,
                "technique": suite_technique,
                "technique_config": {},
                "cases": parsed_cases,
            }
            res = client.create_suite(create_payload)
            st.success(f"Suite registered successfully with ID: `{res.get('id')}`")
        except json.JSONDecodeError as err:
            st.error(f"Invalid JSON syntax in test cases: {err}")
        except Exception as exc:
            st.error(f"Failed to create suite: {exc}")

# --- TAB 3: MANAGE SUITES ---
with tab_manage:
    st.subheader("Registered Test Suites")
    manage_suites = client.list_suites(limit=100)
    items = manage_suites.get("items", [])

    if not items:
        st.info("No test suites found.")
    else:
        for it in items:
            s_id = it.get("id", "")
            s_obj = it.get("suite", {})
            s_name = s_obj.get("name", "")
            s_desc = s_obj.get("description", "")
            case_cnt = len(s_obj.get("cases", []))

            col_info, col_del = st.columns([5, 1])
            with col_info:
                st.markdown(f"**{s_name}** (`{s_id[:8]}...`) — {case_cnt} test cases")
                if s_desc:
                    st.caption(s_desc)
            with col_del:
                if st.button("🗑️ Delete", key=f"del_{s_id}"):
                    client.delete_suite(s_id)
                    st.rerun()
            st.divider()
