from __future__ import annotations

import pandas as pd
import streamlit as st

from .ui_shared import DEFAULT_INPUT_ROOT, load_runs, run_pipeline, save_uploaded_artifact

st.set_page_config(page_title="PBIP Review Dashboard", layout="wide")
st.title("PBIP Review Dashboard")


@st.cache_data(show_spinner=False)
def fetch_runs():
    return load_runs()


def refresh_runs():
    fetch_runs.clear()
    return fetch_runs()


with st.sidebar:
    st.header("Pipeline Controls")
    uploaded_file = st.file_uploader(
        "Upload PBIP bundle or JSON",
        type=["pbip", "zip", "json"],
        help="Uploaded artifacts are stored in pbip_staging/input and processed immediately.",
    )
    if uploaded_file is not None:
        saved = save_uploaded_artifact(uploaded_file.getbuffer(), uploaded_file.name)
        with st.spinner("Running pbip_staging.pilot_pipeline..."):
            result = run_pipeline([saved["artifact_path"]])
        if result["success"]:
            st.success(f"{saved['message']}\n\nPipeline completed successfully.")
            refresh_runs()
            st.experimental_rerun()
        else:
            st.error("Pipeline failed on uploaded artifact.")
            if result["stderr"]:
                st.error(result["stderr"])

    if st.button("Run pipeline on staging/input"):
        with st.spinner("Running pbip_staging.pilot_pipeline..."):
            result = run_pipeline([DEFAULT_INPUT_ROOT])
        if result["success"]:
            st.success("Pipeline completed successfully.")
            refresh_runs()
        else:
            st.error("Pipeline failed.")
            if result["stderr"]:
                st.error(result["stderr"])

runs = fetch_runs()

if not runs:
    st.info("No review artifacts found in pbip_artifacts/reviews. Run the pipeline to generate data.")
    st.stop()

run_labels = [run["label"] for run in runs]
label_to_run = {run["label"]: run for run in runs}

def_index = 0
selected_label = st.sidebar.selectbox("Review run", run_labels, index=def_index)
selected_run = label_to_run[selected_label]
summary = selected_run["summary"]
standards = selected_run.get("standards", {})
issue_count = selected_run.get("issue_count", 0)

st.subheader("Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Domain", summary.get("classification", {}).get("domain", "unknown"))
col2.metric("Intent", summary.get("classification", {}).get("intent", "n/a"))
col3.metric("Measures", summary.get("structure_summary", {}).get("measures", 0))
col4.metric("Issues", issue_count or 0)

st.markdown("### Standards Findings")
issues = standards.get("issues", [])
if issues:
    issue_df = pd.DataFrame(issues)
    st.dataframe(issue_df, use_container_width=True)
else:
    st.success("No standards issues detected for this run.")

auto_fixes = standards.get("auto_fixes", [])
if auto_fixes:
    st.markdown("### Auto-fix Suggestions")
    st.dataframe(pd.DataFrame(auto_fixes), use_container_width=True)

rule_summary = selected_run.get("rule_summary", [])
if rule_summary:
    st.markdown("### Issues per rule")
    st.dataframe(pd.DataFrame(rule_summary), use_container_width=True)

if selected_run.get("recommended_tmdl"):
    st.markdown("### Recommended TMDL Patch")
    st.code(selected_run["recommended_tmdl"], language="sql")

with st.expander("Session history"):
    st.json(selected_run.get("session_history", {}))

with st.expander("Audit trail"):
    st.json(selected_run.get("audit", {}))

with st.expander("Summary payload"):
    st.json(summary)
