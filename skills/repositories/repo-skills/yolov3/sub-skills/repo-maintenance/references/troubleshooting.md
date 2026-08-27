# Maintenance Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Reviewer rejects added guard/helper | Change handled a symptom instead of owner logic | Relocate or delete the wrong path; prefer smaller owner-level edits. |
| CI fails only on Python 3.8 or old torch | New API lacks compatibility gate | Replace with older compatible API or add a narrow version gate. |
| Ruff/docformatter churn | Formatting source of truth is `pyproject.toml` | Run configured tooling; do not fight automated Ultralytics formatting commits. |
| Package editable install fails | `[project]` metadata lacks a version | Decide whether to add version metadata intentionally; otherwise document checkout usage. |
| Export change breaks inference suffix detection | `export_formats()` rows are positionally coupled to runtime detection | Update export and DetectMultiBackend evidence together and run export/deploy checks. |
| PR branch diverges after bot commit | Ultralytics Actions pushed formatting/header commit | `git pull --rebase`, then address findings without reverting bot commits. |
