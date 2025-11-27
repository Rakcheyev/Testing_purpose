# PBIP Intake Folder

Place PBIP exports (either full `.pbip` bundles or JSON exports such as `model.json`) in this directory when running the local review pipeline.

The CLI automatically scans this folder when you run `python -m pbip_staging.pilot_pipeline` without explicit paths. You may also point the command to any other file or directory to process specific artefacts:

```bash
python -m pbip_staging.pilot_pipeline /path/to/report.pbip another/folder/
```

Metadata is optional. If you provide a `metadata.json` file next to the PBIP export (for example `report.pbip` and `report.metadata.json`), the pipeline використовує його разом з евристиками для більш точних рекомендацій.
