---
name: cli-and-formats
description: "Route Docling CLI work, construct safe local conversion commands,
  and choose supported input/output formats and image modes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Docling CLI and Formats

Use this sub-skill when an agent needs to run or explain Docling's local CLI (`docling`), select `--from` / `--to` formats, process local files, URLs, or directories, control CLI output files, or reason about image export and HTML/EPUB image fetching.

Do not use this sub-skill for:

- Python `DocumentConverter` / `convert_string` code; use the conversion sub-skill.
- `docling convert-remote`, `DoclingServiceClient`, or service URL/API key setup; use the remote-service-client sub-skill.
- Pipeline internals, backend tuning, or model-option construction beyond CLI flag routing; use pipeline-configuration/advanced-pipelines.

## Quick Routing

- Prefer `docling SOURCE` for simple local conversion to Markdown in the current directory.
- Use repeated `--to` flags for multiple outputs, for example `--to md --to json`.
- Use repeated `--from` flags to restrict accepted input formats and to filter directory walks, for example `--from pdf --from docx`.
- Use `--output DIR` whenever the command should not write files into the current working directory.
- Use `--image-export-mode referenced` for Markdown/HTML/JSON/YAML outputs when outputs should reference exported image files instead of embedding base64.
- Add `--html-image-fetch local` for trusted local HTML/EPUB assets; use `remote` or `all` only when remote image fetching is intended and safe.

## References

- `references/cli-reference.md`: command anatomy, common recipes, output behavior, and `docling-tools` model-download awareness.
- `references/format-guide.md`: supported input/output format names, output suffixes, and `--from` / `--to` selection rules.
- `references/troubleshooting.md`: CLI dependency, image, directory, output, ASR/VLM, and WebVTT troubleshooting.
- `scripts/build_docling_command.py`: prints a shell-safe `docling` command from structured arguments.

## Command Builder

Use the bundled script to construct command lines without hand-quoting mistakes:

```bash
python scripts/build_docling_command.py SOURCE --output out --to md --to json --from pdf --from docx --image-export-mode referenced
```

The script prints only the command; it does not execute Docling. Pass `--help` for all supported builder options.
