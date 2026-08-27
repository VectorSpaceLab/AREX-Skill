---
name: repo-development
description: "Maintain the Kiln checkout safely: monorepo layout, code style,
  check selection, frontend design standards, local maintenance skills, release
  boundaries, and human/legal gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Repo development

Use this sub-skill when the task is about safe maintenance of the Kiln checkout itself: monorepo layout, repository-wide code quality rules, check/test selection, frontend visual and interaction standards, local maintenance skill boundaries, prerelease/deprecation/release-report procedures, or human/legal gates.

Route product API, datamodel, provider execution, RAG, eval, optimization, and fine-tuning workflows to their owning sub-skills. Route core `.kiln` object modeling to `project-datamodel`; REST/MCP/desktop/web API behavior to `server-desktop-web-api`; model/provider/tool execution semantics to `task-execution-providers-tools`; documents/RAG/vector stores to `rag-documents-data`; and evals, synthetic data, prompt optimization, and fine-tuning behavior to `evals-optimization-finetuning`.

Do not use this sub-skill to run optional paid provider checks, prerelease smoke tests, Ollama checks, cloud/Copilot probes, Slack posts, or other credentialed/outward-facing actions unless the user explicitly asks and the required services are available. Do not perform import/export of generated skills from here.

## Load these references

1. Read [maintainer-workflows.md](references/maintainer-workflows.md) for monorepo layout, code-style rules, API review boundaries, release/deprecation boundaries, and human/legal gates.
2. Read [test-selection.md](references/test-selection.md) to choose targeted Python, server, web, OpenAPI, full, paid, prerelease, slow, and Ollama checks based on changed files.
3. Read [frontend-guidance.md](references/frontend-guidance.md) before changing Svelte UI, controls, cards, tables, visual styling, copy, empty states, or web tests.
4. Read [existing-local-skills.md](references/existing-local-skills.md) when a task resembles model-list maintenance, deprecation audits, prerelease release-candidate checks, or release digests.
5. Read [troubleshooting.md](references/troubleshooting.md) when repository checks, workspace imports, Starlette/FastAPI compatibility, MCP imports, RAG optional imports, web tooling, schema freshness, or credentialed services fail.

## Safe bundled helper

Use [kiln_repo_checks.sh](scripts/kiln_repo_checks.sh) from a Kiln checkout to list or run non-destructive recommended commands:

```bash
bash skills/disco/kiln/sub-skills/repo-development/scripts/kiln_repo_checks.sh --list
bash skills/disco/kiln/sub-skills/repo-development/scripts/kiln_repo_checks.sh --scope python
bash skills/disco/kiln/sub-skills/repo-development/scripts/kiln_repo_checks.sh --scope schema --run
bash skills/disco/kiln/sub-skills/repo-development/scripts/kiln_repo_checks.sh --scope web --run
```

The helper prints commands by default. `--run` executes only safe scopes unless `--allow-paid` is also provided for optional paid/prerelease/Ollama scopes.

## Operating rules

- Inspect the changed files before choosing checks; start with targeted checks for the touched area, then run `uv run ./checks.sh --agent-mode` or the staged variant before finalizing broad changes.
- Keep Python strongly typed, async-first where practical, Pydantic v2-compatible, and compatible with the relevant package target: library code supports Python 3.10+, desktop code targets the desktop runtime.
- Keep Svelte code on Svelte 4 patterns, Tailwind, DaisyUI, and existing Kiln controls. Prefer the established controls and visual language over custom styling.
- Regenerate or check the OpenAPI web client after route, Pydantic request/response model, path/query parameter, or API schema changes.
- Treat `paid`, `prerelease`, `slow`, and `ollama` pytest markers as explicit gates. Default test runs skip paid, slow, and Ollama tests; prerelease is a curated paid subset and needs credentials.
- Do not make legal or signing decisions: no CLA attestations, license tags, license files, or copyleft dependency approvals. Escalate those to a human.
- Do not post public/team messages, run provider-costing checks, or change release/deprecation status without user confirmation.
- Use repo-relative source paths only as evidence notes. Runtime instructions in this skill link only within this sub-skill subtree.

## Evidence notes

This sub-skill is distilled from repo-relative evidence in `AGENTS.md`, `specs/monorepo.md`, `checks.sh`, `pyproject.toml`, `conftest.py`, `app/web_ui/package.json`, `.agents/python_test_guide.md`, `.agents/frontend_design_guide.md`, `.agents/frontend_controls.md`, `.agents/card_style.md`, `.agents/tables_style.md`, `.agents/api_code_review.md`, `.agents/code_review_guidelines.md`, and the local maintenance skill frontmatter under `.agents/skills/`. Verified package evidence covered `kiln-ai`, `kiln-server`, and `kiln-studio-desktop` 1.0.4, CLI commands `kiln_ai`, `kiln_server`, and `kiln_mcp`, core datamodel signatures, `adapter_for_task`, and server route registration.
