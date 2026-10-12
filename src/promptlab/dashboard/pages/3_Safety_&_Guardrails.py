"""Safety and Guardrails Testing Dashboard.

This page provides adversarial prompt injection audits and real-time PII/secret
scanning with text sanitization.
"""

import streamlit as st

from promptlab.dashboard.api_client import PromptLabClient

st.set_page_config(page_title="Safety & Guardrails - PromptLab", page_icon="🛡️", layout="wide")


def get_client() -> PromptLabClient:
    """Retrieve API client."""
    if "client" not in st.session_state:
        st.session_state.client = PromptLabClient()
    return st.session_state.client  # type: ignore[no-any-return]


client = get_client()

st.title("🛡️ Safety & Guardrails Playground")
st.caption(
    "Audit models for prompt injection vulnerabilities and scan text for sensitive data leaks."
)

tab_injection, tab_pii, tab_reports = st.tabs(
    [
        "🎯 Adversarial Injection Audit",
        "🔍 Real-time PII & Secrets Scanner",
        "📜 Historical Safety Reports",
    ]
)

# --- TAB 1: INJECTION AUDIT ---
with tab_injection:
    st.subheader("Prompt Injection Vulnerability Assessment")
    st.write(
        "Tests target models against 16 adversarial prompt injection attack vectors "
        "(direct overrides, delimiter hijacking, roleplay jailbreaks, encoding vectors) "
        "using canary token extraction detection."
    )

    col_ctrl1, col_ctrl2 = st.columns(2)
    with col_ctrl1:
        models = client.list_models()
        target_model = st.selectbox("Target Model for Audit", models, index=0)
    with col_ctrl2:
        canary_token = st.text_input("Custom Canary Token", value="CANARY_SECRET_98765")

    if st.button("🚀 Launch Injection Audit", type="primary", use_container_width=True):
        with st.spinner(f"Running adversarial attacks against {target_model}..."):
            try:
                audit_res = client.run_injection_test(
                    model=target_model,
                    canary=canary_token,
                )

                st.success("Adversarial audit completed!")

                # Risk Summary KPIs
                col_k1, col_k2, col_k3 = st.columns(3)
                tested_cnt = audit_res.get("tested_count", 0)
                breached_cnt = audit_res.get("breached_count", 0)
                risk_lvl = "HIGH RISK" if breached_cnt > 0 else "LOW RISK (PASS)"

                col_k1.metric("Attacks Tested", tested_cnt)
                col_k2.metric("Breaches Detected", breached_cnt)
                if breached_cnt > 0:
                    col_k3.error(f"Risk Rating: {risk_lvl}")
                else:
                    col_k3.success(f"Risk Rating: {risk_lvl}")

                st.divider()

                # Detailed Attack Breakdown
                st.subheader("Attack Vector Analysis")
                results_list = audit_res.get("results", [])

                for r in results_list:
                    vec_id = r.get("vector_id", "")
                    category = r.get("category", "")
                    breached = r.get("breached", False)
                    prompt = r.get("prompt", "")
                    output = r.get("output", "")

                    status_icon = "🚨 BREACHED" if breached else "🛡️ DEFENDED"
                    expander_label = f"[{category.upper()}] Vector {vec_id} — {status_icon}"

                    with st.expander(expander_label, expanded=breached):
                        st.markdown("**Attack Prompt:**")
                        st.code(prompt, language="markdown")
                        st.markdown("**Model Completion:**")
                        st.code(output, language="markdown")
                        if breached:
                            st.error("Canary secret was extracted by this attack vector!")
                        else:
                            st.success("Target model did not leak the canary secret.")

            except Exception as exc:
                st.error(f"Audit failed: {exc}")

# --- TAB 2: PII SCANNER ---
with tab_pii:
    st.subheader("Real-Time PII & Credential Sanitizer")
    st.write(
        "Detect and redact sensitive entities: Emails, Phone numbers (Indian & International), "
        "IPv4 addresses, Credit Cards (Luhn verified), and API keys (Groq, OpenAI, AWS)."
    )

    sample_col1, sample_col2 = st.columns(2)
    with sample_col1:
        if st.button("Load Leaky Sample (API Key & PII)"):
            st.session_state.scan_input = (
                "Please send the confidential report to alice.johnson@enterprise.io or call "
                "+91 98765 43210. Connect via 192.168.1.100 using API key gsk_abcdef1234567890abcdef."
            )
    with sample_col2:
        if st.button("Load Safe Sample"):
            st.session_state.scan_input = (
                "Hello! Can you help me write a Python function to sort a list?"
            )

    text_to_scan = st.text_area(
        "Input Payload to Inspect",
        value=st.session_state.get(
            "scan_input", "Contact user at test@example.com with key sk-1234567890abcdef."
        ),
        height=120,
    )

    if st.button("🔍 Scan & Sanitize", type="primary"):
        if not text_to_scan.strip():
            st.warning("Please provide text to scan.")
        else:
            try:
                scan_res = client.scan_text(text_to_scan)
                risk = scan_res.get("risk_level", "low").upper()
                passed = scan_res.get("passed", True)
                findings = scan_res.get("pii_findings", [])
                redacted = scan_res.get("redacted_text", "")

                col_res1, col_res2 = st.columns([1, 2])
                with col_res1:
                    if passed:
                        st.success(f"Payload Verdict: SAFE (Risk: {risk})")
                    else:
                        st.error(f"Payload Verdict: BREACH / LEAK (Risk: {risk})")
                    st.metric("Detected Findings", len(findings))

                with col_res2:
                    st.subheader("Sanitized Payload")
                    st.code(redacted, language="markdown")

                st.divider()

                if findings:
                    st.subheader("Identified Leaks & Entities")
                    for f in findings:
                        entity_type = f.get("type", "").upper()
                        val = f.get("value", "")
                        start = f.get("start", 0)
                        end = f.get("end", 0)
                        st.markdown(f"- **{entity_type}**: `{val}` *(Position {start}:{end})*")
                else:
                    st.info("No sensitive entities or API credentials detected.")

            except Exception as exc:
                st.error(f"Scan failed: {exc}")

# --- TAB 3: HISTORICAL REPORTS ---
with tab_reports:
    st.subheader("Historical Safety Audits")
    rep_data = client.list_safety_reports(limit=50)
    rep_items = rep_data.get("items", [])

    if not rep_items:
        st.info("No historical safety reports found.")
    else:
        for rep in rep_items:
            rid = rep.get("id", "")
            rmodel = rep.get("model", "")
            rrisk = rep.get("risk_level", "low").upper()
            rpassed = rep.get("passed", True)
            inj_res = rep.get("injection_results", [])

            badge = "✅ PASSED" if rpassed else "🚨 FAILED"
            with st.expander(f"Report [{rid[:8]}...] — {rmodel} — {badge} (Risk: {rrisk})"):
                st.write(f"Total Attack Vectors Audited: {len(inj_res)}")
                breaches = [x for x in inj_res if x.get("breached")]
                st.write(f"Breaches Count: {len(breaches)}")
