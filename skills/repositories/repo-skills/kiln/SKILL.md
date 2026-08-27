---
name: kiln
description: "Use and maintain Kiln's AI development monorepo: Python library,
  REST/MCP server, desktop studio server, Svelte web UI, RAG, evals,
  fine-tuning, providers, tools, and repo checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Kiln Repo Skill

Use this skill when a task involves Kiln, the `kiln-ai` Python library, the `kiln-server` REST/MCP server, the desktop studio server, or the Svelte web UI. Kiln is a monorepo for building AI systems: projects/tasks/runs, evals, synthetic data, prompt optimization, RAG/documents/search, fine-tuning, tools/MCP, skills, providers/models, Git sync, desktop app, and web UI all share the same `.kiln` data model.

## First checks

1. If working in a checkout, read [references/repo-provenance.md](references/repo-provenance.md) before assuming this skill is current.
2. For package use, start with a normal install/import check:
   ```bash
   pip install kiln-ai kiln-server
   python - <<'PY'
   import kiln_ai
   from kiln_ai.datamodel import Project, Task
   from kiln_server.server import make_app
   print(Project, Task, len(make_app().routes))
   PY
   ```
3. For checkout maintenance, use [scripts/check_kiln_environment.py](scripts/check_kiln_environment.py) for safe import/CLI probes and [scripts/kiln_repo_checks.sh](scripts/kiln_repo_checks.sh) to print targeted check commands.
4. Do not run paid, prerelease, Ollama, Copilot, cloud-provider, desktop signing, release-posting, or other credentialed/destructive workflows unless the user explicitly authorizes them and supplies the required services.

## Route by task

- Read [sub-skills/project-datamodel/SKILL.md](sub-skills/project-datamodel/SKILL.md) for `.kiln` files, `Project`, `Task`, `TaskRun`, prompts, dataset splits, skills, JSON schemas, input transforms, and `kiln_ai package_project`.
- Read [sub-skills/task-execution-providers-tools/SKILL.md](sub-skills/task-execution-providers-tools/SKILL.md) for running tasks with LiteLLM or MCP, run configs, model/provider registries, structured outputs, thinking levels, tools, skills, RAG tool references, and MCP sessions.
- Read [sub-skills/rag-documents-data/SKILL.md](sub-skills/rag-documents-data/SKILL.md) for document ingestion, extraction, chunking, embeddings, LanceDB/vector stores, rerankers, RAG configs, indexing, and search tools.
- Read [sub-skills/evals-optimization-finetuning/SKILL.md](sub-skills/evals-optimization-finetuning/SKILL.md) for evals, G-Eval, statistics, synthetic data/data guides, repair, prompt optimization, dataset splits, and fine-tuning.
- Read [sub-skills/server-desktop-web-api/SKILL.md](sub-skills/server-desktop-web-api/SKILL.md) for FastAPI routes, `kiln_server`, `kiln_mcp`, desktop studio server extensions, Git sync, jobs/SSE/chat, OpenAPI generation, Svelte stores/components/routes, and schema-to-frontend flows.
- Read [sub-skills/repo-development/SKILL.md](sub-skills/repo-development/SKILL.md) for monorepo layout, test selection, lint/type/format/build commands, frontend design rules, existing local maintenance skills, prerelease/deprecation boundaries, and human/legal gates.

## Cross-cutting rules

- Treat `libs/core` as the canonical Python library (`kiln-ai`) and source of model/datamodel/runtime truth.
- Treat `libs/server` as the public REST/MCP server package (`kiln-server`) wrapping core APIs.
- Treat `app/desktop` as checkout-bound desktop/studio-server code; it extends the server and hosts the built web UI.
- Treat `app/web_ui` as Svelte 4 + TypeScript + Tailwind/DaisyUI. Backend API changes usually require OpenAPI schema regeneration/checks.
- Prefer source and installed-package facts over README guesses. Use tests to confirm edge behavior and expected errors.
- Use mocked/local tests for normal verification. Paid/prerelease/provider/Ollama/cloud cases are coverage gaps unless intentionally authorized.

## Common setup gotchas

- Current Kiln code expects lock-compatible dependencies. In particular, unconstrained installs may choose incompatible `mcp` or `starlette` versions; use the repo lock or pin to the versions described in [references/troubleshooting.md](references/troubleshooting.md) when debugging imports.
- RAG/LanceDB imports can require `pandas` via `llama-index-vector-stores-lancedb` even when a minimal dependency resolver misses it.
- Desktop source imports are checkout workflows, not isolated public wheel imports; do not confuse `kiln-studio-desktop` metadata with the full source tree being available.

## Repo-level references and helpers

- [references/repo-development-overview.md](references/repo-development-overview.md) summarizes monorepo packages, install surfaces, and cross-skill ownership.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting install/import/check failures before diving into sub-skill-specific troubleshooting.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) is structured router metadata for managed repo-skill import tooling.
- [scripts/check_kiln_environment.py](scripts/check_kiln_environment.py) safely checks package imports, distribution metadata, CLI help, and optional checkout-aware probes.
- [scripts/kiln_repo_checks.sh](scripts/kiln_repo_checks.sh) prints or runs conservative targeted maintenance commands from a Kiln checkout.
