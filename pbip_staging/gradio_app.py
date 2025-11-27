from __future__ import annotations

from typing import Dict, Tuple

import gradio as gr
import pandas as pd

from .ui_shared import DEFAULT_INPUT_ROOT, load_runs, run_pipeline


def _render_run(label: str | None, run_map: Dict[str, Dict]) -> Tuple[str, pd.DataFrame, pd.DataFrame, str]:
    run = run_map.get(label) if run_map else None
    if not run:
        return "No review run selected.", pd.DataFrame(), pd.DataFrame(), ""

    summary = run.get("summary", {})
    standards = run.get("standards", {})
    classification = summary.get("classification", {})
    overview_lines = [
        f"**Source:** {summary.get('source', 'n/a')}",
        f"**Domain:** {classification.get('domain', 'unknown')}",
        f"**Intent:** {classification.get('intent', 'n/a')}",
        f"**Issues:** {run.get('issue_count', 0)}",
    ]
    tables = summary.get("structure_summary", {}).get("tables", 0)
    measures = summary.get("structure_summary", {}).get("measures", 0)
    columns = summary.get("structure_summary", {}).get("columns", 0)
    overview_lines.append(f"**Model footprint:** {tables} tables · {measures} measures · {columns} columns")

    issues = pd.DataFrame(standards.get("issues", [])) if standards else pd.DataFrame()
    auto_fixes = pd.DataFrame(standards.get("auto_fixes", [])) if standards else pd.DataFrame()
    tmdl_payload = run.get("recommended_tmdl") or ""
    return "\n".join(overview_lines), issues, auto_fixes, tmdl_payload


def _refresh_runs() -> Tuple[gr.Dropdown, Dict[str, Dict], str, pd.DataFrame, pd.DataFrame, str]:
    runs = load_runs()
    run_map = {run["label"]: run for run in runs}
    first_label = next(iter(run_map), None)
    dropdown = gr.Dropdown.update(choices=list(run_map.keys()), value=first_label)
    summary, issues, auto_fixes, tmdl_payload = _render_run(first_label, run_map)
    return dropdown, run_map, summary, issues, auto_fixes, tmdl_payload


def _trigger_pipeline() -> str:
    result = run_pipeline([DEFAULT_INPUT_ROOT])
    status_prefix = "✅ Pipeline completed" if result["success"] else "⚠️ Pipeline failed"
    details = result["stderr"] or result["stdout"] or ""
    if details:
        return f"{status_prefix}.\n\n``{details}``"
    return status_prefix


def build_app() -> gr.Blocks:
    with gr.Blocks(title="PBIP Review Dashboard") as demo:
        gr.Markdown("# PBIP Review Dashboard")
        status_box = gr.Markdown()
        refresh_button = gr.Button("Refresh runs")
        run_button = gr.Button("Run pipeline (staging/input)")
        run_state = gr.State({})
        run_dropdown = gr.Dropdown(label="Select review run", choices=[])
        summary_md = gr.Markdown()
        issues_df = gr.DataFrame(label="Standards issues", interactive=False)
        auto_df = gr.DataFrame(label="Auto-fix suggestions", interactive=False)
        tmdl_code = gr.Code(label="Recommended TMDL patch", language="sql")

        demo.load(
            _refresh_runs,
            outputs=[run_dropdown, run_state, summary_md, issues_df, auto_df, tmdl_code],
        )

        refresh_button.click(
            _refresh_runs,
            outputs=[run_dropdown, run_state, summary_md, issues_df, auto_df, tmdl_code],
        )

        run_dropdown.change(
            _render_run,
            inputs=[run_dropdown, run_state],
            outputs=[summary_md, issues_df, auto_df, tmdl_code],
        )

        run_button.click(_trigger_pipeline, outputs=status_box).then(
            _refresh_runs,
            outputs=[run_dropdown, run_state, summary_md, issues_df, auto_df, tmdl_code],
        )

        demo.queue(concurrency_count=1)
    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="0.0.0.0", server_port=7860)
