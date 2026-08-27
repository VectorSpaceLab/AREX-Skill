# Structured export workflow

Use this reference when producing JSON from NLP-progress Markdown content.

## Inputs

The bundled exporter accepts one or more paths. Each path can be:

- A single Markdown file.
- A directory containing `.md` files.
- A mix of files and directories.

The script expands only one directory level for Markdown files, mirroring the repository utility's intended use for language directories such as `english/`.

## Basic commands

From this sub-skill directory:

```bash
python3 scripts/export_nlp_progress.py /path/to/NLP-progress/english --output english.json
python3 scripts/export_nlp_progress.py /path/to/NLP-progress/english/question_answering.md --output qa.json
python3 scripts/export_nlp_progress.py /path/to/NLP-progress/english /path/to/NLP-progress/vietnamese/vietnamese.md --output subset.json
```

If you copy the bundled script elsewhere, keep paths explicit:

```bash
python3 export_nlp_progress.py /path/to/NLP-progress/chinese --output chinese.json
```

The default output is `structured.json` in the current working directory. Prefer an explicit `--output` path so later steps know where the JSON was written.

## Expected output check

After running, check:

```bash
python3 - <<'PY'
import json
from pathlib import Path
path = Path('english.json')
data = json.loads(path.read_text(encoding='utf-8'))
print(type(data).__name__, len(data))
print(data[0].keys() if data else 'empty')
PY
```

A non-empty language directory should usually produce a JSON list with at least one task object. Very thin pages or pages without H3 dataset sections may still produce tasks with descriptions but no `datasets`.

## Combining with benchmark lookup

For user-facing research answers:

1. Use `benchmark-catalog` to select pages, task headings, and language coverage.
2. Export only the chosen files/directories.
3. Preserve JSON field names and original metric column names.
4. Treat output as a structured representation of the Markdown snapshot, not as an independently verified current leaderboard.

## Combining with content maintenance

For edit/verification tasks:

1. Use `content-maintenance` to apply contribution and table-style rules.
2. Run its Markdown checker on changed files.
3. Export the changed files with this script.
4. Confirm the expected task/dataset/result row appears in JSON.

## No third-party dependencies

The exporter uses only Python standard-library modules: `argparse`, `json`, `os`, `re`, `sys`, `pathlib`, and typing helpers. If Python itself is unavailable, prepare a basic Python 3 environment; do not install ML frameworks or dataset packages for this workflow.
