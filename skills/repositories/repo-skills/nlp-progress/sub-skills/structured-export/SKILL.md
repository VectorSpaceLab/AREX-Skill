---
name: structured-export
description: "Guides NLP-progress structured JSON export, Markdown parser
  assumptions, output schema, bundled export script use, and export
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# structured-export

Use this sub-skill when a user asks to convert NLP-progress Markdown pages into machine-readable JSON, inspect the structured export schema, debug `structured.json`, or preserve the behavior of the repository's Markdown parser.

NLP-progress is not an installable Python package. The export workflow is a standard-library Python script that reads Markdown files or directories and writes JSON. No ML backend, dataset download, accelerator, Ruby runtime, or package install is required.

## Fast workflow

1. Identify the NLP-progress content root or the exact Markdown files/directories the user wants to export.
2. Use the bundled script from this sub-skill directory or copy it to a working area:

   ```bash
   python3 scripts/export_nlp_progress.py <file-or-directory> --output structured.json
   python3 scripts/export_nlp_progress.py english vietnamese/vietnamese.md --output subset.json
   ```

3. Validate the JSON shape with [references/json-schema.md](references/json-schema.md). Expect a top-level list of task objects; nested `subtasks`, `datasets`, `sota`, and `subdatasets` appear only when the source headings/tables support them.
4. Check [references/parser-assumptions.md](references/parser-assumptions.md) before relying on nested H4 sections, unusual table headers, multiple paper links, or multiple SOTA tables in one section.
5. If output is empty, lossy, or noisy, triage with [references/troubleshooting.md](references/troubleshooting.md).

## References and script

- [references/export-workflow.md](references/export-workflow.md) — command patterns, input/output handling, validation, and integration with benchmark/catalog workflows.
- [references/json-schema.md](references/json-schema.md) — field-level output schema and small examples.
- [references/parser-assumptions.md](references/parser-assumptions.md) — heading, table, metric, link, and warning behavior inherited from the repo export utility.
- [references/troubleshooting.md](references/troubleshooting.md) — path errors, malformed tables, empty output, skipped tables, and subdataset mismatch recovery.
- [scripts/export_nlp_progress.py](scripts/export_nlp_progress.py) — bundled standard-library export helper adapted from NLP-progress's `structured/export.py`.

## Boundaries

- For deciding which benchmark page or language directory to export, route to `benchmark-catalog` first.
- For editing Markdown before export, validating contribution style, or optional Jekyll preview, route to `content-maintenance` first.
- Do not run original repository scripts as a runtime dependency. Use the bundled export helper unless the user explicitly wants to compare against a checkout's native utility during verification or maintenance.

## Handoff checklist

When finishing an export task, report:

- Which files/directories were exported.
- Output JSON path and top-level task count.
- Any warnings printed by the exporter.
- Known parser limitations that affect the result, especially H4/nested sections, malformed table headers, or multi-link paper/source cells.
- Whether the result should be treated as a structured snapshot rather than current leaderboard truth.
