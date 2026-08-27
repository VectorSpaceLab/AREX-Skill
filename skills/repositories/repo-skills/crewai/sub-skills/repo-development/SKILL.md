---
name: repo-development
description: "Guides CrewAI repository contributors through monorepo layout,
  workspace package metadata, focused pytest and lint checks, docs versioning,
  release-freeze hazards, and safe native verification selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Repo Development

Use this sub-skill when work is about contributing to the CrewAI monorepo itself: choosing focused checks, understanding workspace packages, editing docs safely, avoiding release/docs snapshot hazards, or selecting safe native verification targets after a code or docs change.

## Read First

- [Contributor guidance](references/contributor-guidance.md) for repository layout, workspace packages, package metadata, contributor workflow, and cross-package dependency pins.
- [Docs maintenance](references/docs-maintenance.md) for Edge docs, frozen snapshots, `docs/docs.json`, image rules, docs validation, and release-freeze no-run guidance.
- [Testing](references/testing.md) for root pytest, ruff, mypy, devtools test configuration, focused command selection, and safe native verification principles.
- [Troubleshooting](references/troubleshooting.md) for frozen-doc edits, image deletions, broad tests, import-mode confusion, workspace pin drift, and accidental release-freeze mutations.
- [Native test selector](scripts/select_native_tests.py) to map changed paths to suggested focused checks without running tests, release scripts, LLMs, credentials, or network calls.

## Boundaries

- Stay here for monorepo contribution mechanics, docs versioning, package workspace metadata, test/lint/type-check selection, docs freeze hazards, and maintainer-only devtools guidance.
- Use [../../SKILL.md](../../SKILL.md) when a request needs root CrewAI scenario routing before deciding whether it is repository-maintenance work or normal CrewAI usage.
- Use [../cli-and-projects/SKILL.md](../cli-and-projects/SKILL.md) for `crewai` CLI behavior, project scaffolding, command semantics, and project template troubleshooting beyond repository test selection.
- Use [../core-runtime/SKILL.md](../core-runtime/SKILL.md) for `Agent`, `Task`, `Crew`, processes, guardrails, callbacks, and runtime semantics.
- Use [../flows-and-events/SKILL.md](../flows-and-events/SKILL.md) for `Flow`, decorators, routers, persistence, event listeners, and hook adjacency.
- Use [../tools-and-mcp/SKILL.md](../tools-and-mcp/SKILL.md), [../memory-knowledge-and-rag/SKILL.md](../memory-knowledge-and-rag/SKILL.md), [../llm-and-providers/SKILL.md](../llm-and-providers/SKILL.md), [../files-and-multimodal/SKILL.md](../files-and-multimodal/SKILL.md), or [../observability-and-hooks/SKILL.md](../observability-and-hooks/SKILL.md) for normal CrewAI package usage and capability-specific API details.

## Safe Operating Defaults

- Prefer the smallest relevant check first: a focused pytest file, `crewai --help`, parser/help output from bundled scripts, `ruff check --no-fix`, or docs link checks.
- Do not edit `docs/v*/` snapshots during normal development; update `docs/edge/<lang>/...` instead.
- Do not delete or rename existing `docs/images/` assets; add a replacement asset and point Edge docs at the new file.
- Treat docs freeze and release automation as no-run unless the task is explicitly a release-cut context with the expected `[docs-freeze]` workflow.
- Use the bundled selector before broad native verification when a task changes both code and docs.

## Usability Targets

- After a CLI command plus docs change, select safe focused checks covering CLI command loading, changed command tests, Edge docs validation, and any docs/devtools impacts without running LLM-backed project execution.
- When updating docs, keep edits in Edge, preserve frozen snapshots, avoid image deletion/renames, update navigation only when needed, and choose validation commands that do not mutate release state.
