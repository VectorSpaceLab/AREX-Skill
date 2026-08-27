---
name: ultra-rag
description: "Routes UltraRAG pipeline orchestration, MCP server workflows, and
  the UI/backend stack."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# UltraRAG

Use this repo skill when a task mentions UltraRAG pipelines, MCP servers, the
web UI, the knowledge-base backend, or the case-study viewer.

UltraRAG is organized around three user-facing workflow families:

1. **Pipeline orchestration** — `ultrarag build`, `ultrarag run`, `ultrarag show`,
   YAML pipelines, `ToolCall`, `PipelineCall`, branching, looping, and the demo
   / experiment pipelines under `examples/`.
2. **MCP server workflows** — the individual servers in `servers/`, their tool
   and prompt signatures, parameter files, and backend-specific configuration.
3. **UI and storage workflows** — the Flask backend under `ui/backend`, chat
   sessions, auth, knowledge-base management, memory sync, and the case-study
   viewer.

## Start here

- Read `references/overview.md` for the verified package shape, install hints,
  and repo map.
- Read `references/repo-provenance.md` when you need to compare this skill to a
  checkout or decide whether to refresh it.
- Read `references/troubleshooting.md` for cross-cutting install, import, and
  runtime failures.
- Use `scripts/check_install.py` for a quick local import check.

## Install and smoke check

Recommended install path:

```bash
uv sync
```

Narrower dependency sets are available when you only need part of the repo:

```bash
uv sync --extra retriever
uv sync --extra generation
uv sync --extra corpus
uv sync --extra evaluation
uv sync --all-extras
```

Editable installs also work:

```bash
uv pip install -e .
uv pip install -e '.[all]'
```

Verified package facts:

- Distribution: `ultrarag`
- Version: `0.3.0.2`
- Python: `>=3.11, <3.13`
- Console entry point: `ultrarag = ultrarag.client:main`

Minimal check:

```bash
python -c "from importlib.metadata import version; print(version('ultrarag'))"
ultrarag --help
```

## Route map

| If the task is about... | Read |
| --- | --- |
| `ultrarag build`, `ultrarag run`, `ultrarag show`, `ToolCall`, `PipelineCall`, YAML step flow, branch/loop logic, example pipelines | `sub-skills/pipelines/SKILL.md` |
| `servers/retriever`, `servers/generation`, `servers/prompt`, `servers/corpus`, `servers/evaluation`, `servers/custom`, `servers/memory`, backend options, tool/prompt signatures, parameter files | `sub-skills/servers/SKILL.md` |
| `ultrarag show ui`, `ultrarag show case`, the Flask backend, chat sessions, KB files, auth, memory sync, storage paths, frontend build/layout | `sub-skills/ui-and-storage/SKILL.md` |

## Shared runtime helpers

- `scripts/check_install.py` — quick import/version check for the installed
  package.

## Notes for future agents

- Keep workflow instructions inside the generated skill tree; do not depend on
  the original checkout being open.
- Use the sub-skill that matches the user intent first, then open the nearest
  reference file for command details, backend notes, and troubleshooting.
- If a task spans multiple families, read the overlapping sub-skills instead of
  guessing from source layout.
