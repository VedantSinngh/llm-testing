"""Interactive Prompt Playground for rapid engineering and evaluation.

This page allows engineers to experiment with prompt techniques, sampling hyperparameters,
and evaluation rubrics on individual prompts in real time.
"""

from typing import Any

import streamlit as st

from promptlab.dashboard.api_client import PromptLabClient

st.set_page_config(page_title="Playground - PromptLab", page_icon="🎯", layout="wide")


def get_client() -> PromptLabClient:
    """Retrieve or initialize API client."""
    if "client" not in st.session_state:
        st.session_state.client = PromptLabClient()
    return st.session_state.client  # type: ignore[no-any-return]


client = get_client()

st.title("🎯 Prompt Engineering Playground")
st.caption("Test prompt formulations, techniques, and evaluation scorers on individual queries.")

# Sidebar Configuration
st.sidebar.header("⚙️ Generation Parameters")
models = client.list_models()
selected_model = st.sidebar.selectbox("Target Model", models, index=0)

temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.05)
top_p = st.sidebar.slider("Top-P", min_value=0.0, max_value=1.0, value=1.0, step=0.05)
max_tokens = st.sidebar.slider("Max Tokens", min_value=32, max_value=2048, value=512, step=32)

st.sidebar.divider()
st.sidebar.header("🧠 Prompt Technique")
technique = st.sidebar.selectbox(
    "Technique",
    ["zero_shot", "few_shot", "chain_of_thought", "structured_output"],
    index=0,
)

technique_config: dict[str, Any] = {}
if technique == "few_shot":
    st.sidebar.subheader("Few-Shot Demonstrations")
    ex1_in = st.sidebar.text_input("Example 1 Input", value="Great product!")
    ex1_out = st.sidebar.text_input("Example 1 Output", value="Positive")
    technique_config["examples"] = [{"input": ex1_in, "output": ex1_out}]
elif technique == "structured_output":
    st.sidebar.subheader("Target Schema Definition")
    schema_str = st.sidebar.text_area(
        "JSON Schema (Properties)",
        value='{\n  "sentiment": "positive | negative",\n  "confidence": 0.95\n}',
        height=100,
    )
    technique_config["schema"] = schema_str

# Main playground layout
col_input, col_scorer = st.columns([2, 1])

with col_input:
    system_prompt = st.text_input(
        "System Prompt (Optional)",
        value="You are an expert, concise AI assistant.",
        placeholder="Enter behavioral guidelines...",
    )
    user_prompt = st.text_area(
        "User Prompt",
        value="Classify the sentiment of: 'The customer support resolved my issue in under 5 minutes!'",
        height=140,
        placeholder="Enter user query...",
    )

with col_scorer:
    st.subheader("🧪 Scorer Setup")
    scorer_type = st.selectbox(
        "Scorer",
        ["contains", "exact_match", "regex_match", "json_valid", "sql_result"],
        index=0,
    )
    expected_output = st.text_input(
        "Expected Output / Substring",
        value="positive",
        placeholder="Target ground truth...",
    )
    scorer_config: dict[str, Any] = {}
    if scorer_type == "contains":
        scorer_config = {"substring": expected_output, "case_sensitive": False}
    elif scorer_type == "exact_match":
        scorer_config = {"case_sensitive": False}
    elif scorer_type == "regex_match":
        scorer_config = {"pattern": r"(?i)positive"}

run_btn = st.button("🚀 Run Generation & Evaluation", type="primary", use_container_width=True)

if run_btn:
    if not user_prompt.strip():
        st.warning("Please provide a prompt to execute.")
    else:
        with st.spinner("Generating completion and evaluating..."):
            # Construct inline evaluation suite
            suite_payload = {
                "name": "playground_adhoc_run",
                "system_prompt": system_prompt if system_prompt.strip() else None,
                "technique": technique,
                "technique_config": technique_config,
                "cases": [
                    {
                        "id": "play-case-1",
                        "input": user_prompt,
                        "expected": expected_output if expected_output.strip() else None,
                        "scorer": scorer_type,
                        "scorer_config": scorer_config,
                        "tags": ["playground"],
                    }
                ],
            }

            request_payload = {
                "suite": suite_payload,
                "model": selected_model,
                "params": {
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_tokens": max_tokens,
                },
            }

            try:
                run_result = client.execute_run(request_payload)
                case_result = run_result["case_results"][0]
                resp = case_result["response"]

                st.success("Execution completed successfully!")

                # Latency & Token KPI Cards
                col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                col_kpi1.metric("Latency", f"{resp.get('latency_ms', 0):.1f} ms")
                col_kpi2.metric("Prompt Tokens", resp.get("prompt_tokens", 0))
                col_kpi3.metric("Completion Tokens", resp.get("completion_tokens", 0))
                col_kpi4.metric("Total Tokens", resp.get("prompt_tokens", 0) + resp.get("completion_tokens", 0))

                st.divider()

                # Model Completion Card
                st.subheader("Generated Completion")
                response_text = resp.get("text", "")

                # Handle Chain-of-Thought reasoning separation if present
                if "<thought>" in response_text and "</thought>" in response_text:
                    thought = response_text.split("<thought>")[1].split("</thought>")[0].strip()
                    final_ans = response_text.split("</thought>")[1].strip()
                    with st.expander("💭 Step-by-Step Reasoning (<thought>)", expanded=True):
                        st.write(thought)
                    st.code(final_ans, language="markdown")
                else:
                    st.code(response_text, language="markdown")

                # Evaluation Outcome
                st.subheader("Evaluation Score")
                score_passed = case_result.get("passed", False)
                score_val = case_result.get("score", 0.0)
                reason = case_result.get("reason", "")

                if score_passed:
                    st.success(f"PASSED — Score: {score_val:.2f} / 1.00 — {reason}")
                else:
                    st.error(f"FAILED — Score: {score_val:.2f} / 1.00 — {reason}")

            except Exception as exc:
                st.error(f"Execution failed: {exc}")
