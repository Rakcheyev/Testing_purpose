# Pilot PBIP Cases

This folder contains curated scenarios for demonstrating the MCP review workflow on a small set of PBIP projects. Each case has:

- `metadata.json` with the business context, owners, checkpoints, and target standards.
- `input/` directory where the raw PBIP export (JSON or official `.pbip` bundle) is placed for processing.
- `notes.md` for analyst findings or follow-up.

Run `python -m pbip_staging.pilot_pipeline --case <case_id>` to execute the local workflow without hitting HTTP APIs.
