# CLI and interactive search

JioNLP exposes one small console helper and one interactive Python helper:

- `jio_help` — console entry point that opens the interactive keyword search.
- `python -c "import jionlp as jio; jio.help()"` — same interactive search from Python.
- `python scripts/search_api_docs.py KEYWORD ...` — noninteractive search across public docstrings.

## How the search works
- The search is docstring-driven.
- Use Chinese keywords when possible; the helper scores docstrings by keyword matches.
- Multi-word queries are allowed; the search returns the best matches first.

## When to use it
- You know the task family but not the exact function name.
- You want to discover whether a feature is exposed as a root attribute or under a submodule such as `jio.ner`, `jio.cws`, `jio.pos`, `jio.textaug`, or `jio.bpe`.

## Notes
- The helper is interactive by design, so it is not ideal for scripted smoke tests.
- The bundled `scripts/search_api_docs.py` wrapper is the preferred noninteractive option.
