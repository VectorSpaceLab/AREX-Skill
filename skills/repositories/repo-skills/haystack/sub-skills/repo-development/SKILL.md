---
name: repo-development
description: "Work safely inside the Haystack checkout with Hatch, focused
  tests, formatting, typing, release notes, docs checks, and contribution
  conventions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Repo Development

Use this sub-skill when the task changes the Haystack repository itself rather than building an application with the public `haystack-ai` package.

## Route Here

- Prepare or validate the development environment before running repository commands.
- Pick and run focused unit or integration tests after changing `haystack/`, `test/`, docs, release notes, or scripts.
- Run formatting, linting, type checks, release-note creation, or docs contribution checks.
- Decide whether a change needs tests, docs updates, and a `releasenotes/notes/` entry.
- Troubleshoot Hatch, pytest, optional dependency, credential/backend, data/config, or docs workflow failures inside this checkout.

## Reroute

- Public `Pipeline`, `AsyncPipeline`, `SuperComponent`, or `@component` usage workflows: `../pipelines-and-components/SKILL.md`.
- File conversion, `Document`, `ByteStream`, preprocessing, routing, and ingestion flows: `../data-ingestion/SKILL.md`.
- Retrieval, document stores, rankers, and RAG design: `../retrieval-and-rag/SKILL.md`.
- Generator, embedder, model-provider, or credential setup for package users: `../generation-and-model-components/SKILL.md`.
- Agent, tool invocation, and human-in-the-loop runtime workflows: `../agents-tools-and-hitl/SKILL.md`.

## First Checks

1. From the repository root, verify Hatch is available with `hatch --version`; do not run repository Python commands with bare `python` or install packages with bare `pip`.
2. For scripts that need test dependencies, use `hatch -e test run python path/to/script.py`.
3. Prefer the smallest meaningful validation first, then broaden only if the change affects shared infrastructure.
4. If editing docs under `docs-website/`, also consult `references/commands.md#docs-changes` before choosing Node/Docusaurus checks.

## Reference Map

- Use `references/commands.md` for command selection, test scope, release notes, docs edits, and PR-ready checks.
- Use `references/troubleshooting.md` when Hatch, imports, optional dependencies, credentials/backends, API misuse, fixtures, docs builds, or release notes fail.
- Run `scripts/focused_test_suggester.py` with changed paths to get conservative Hatch commands for common areas:

```bash
python sub-skills/repo-development/scripts/focused_test_suggester.py haystack/components/routers/file_type_router.py test/components/routers/test_file_router.py
```

The helper only prints suggestions; it does not inspect private state, mutate files, or require the original checkout beyond the paths you pass.

## Fast Decision Pattern

- Code behavior change in `haystack/`: add or update nearby tests, run a focused `hatch run test:unit ...`, then consider `hatch run test:types` and `hatch run fmt`.
- Integration/backend change: run the closest integration test with `hatch run test:integration path::node` only when required services or credentials are available; otherwise document the skip.
- User-facing code, dependency, or behavior change: create a release note with `hatch run release-note short-description` and edit the generated YAML using reStructuredText.
- Docs change: edit `docs-website/docs/` for next release; for stable-doc fixes, also edit the highest `docs-website/versioned_docs/version-*` copy and update `sidebars.js` when adding or moving pages.
