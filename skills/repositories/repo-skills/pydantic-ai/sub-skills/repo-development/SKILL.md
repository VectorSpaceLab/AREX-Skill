---
name: repo-development
description: "Guides maintainers through Pydantic AI repository development,
  contribution rules, workspace layout, targeted validation, VCR cassettes, docs
  tests, PR conventions, and generated skill refreshes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Repo Development

Use this sub-skill when editing, reviewing, testing, documenting, or preparing changes to the Pydantic AI monorepo itself.

## Read First

- Read [references/repository-layout.md](references/repository-layout.md) to map the workspace packages, source roots, tests, docs, scripts, local workflow skills, and generated runtime skills.
- Read [references/contribution-guidelines.md](references/contribution-guidelines.md) before changing public APIs, behavior, docs, examples, dependencies, generated skills, or maintainer workflows.
- Read [references/testing-and-cassettes.md](references/testing-and-cassettes.md) to choose targeted `pytest`, `pyright`, `ruff`, docs-example, VCR cassette, and snapshot commands.
- Read [references/troubleshooting.md](references/troubleshooting.md) when full validation is slow, provider recordings fail, snapshots drift, optional dependencies skip, docs examples fail, or generated skills become stale.
- Run [scripts/check_repo_context.py](scripts/check_repo_context.py) for a safe, read-only summary of the checkout, package workspace, test/cassette coverage, cassette pairing candidates, and likely validation targets.

## Route Elsewhere

- Use `../agent-core/` when source changes affect `Agent`, `RunContext`, run modes, dependencies, streaming, message history, or deterministic agent tests.
- Use `../tools-and-toolsets/` when source changes affect function tools, tool schemas, toolsets, approvals, deferred tools, retries, or tool search.
- Use `../outputs-and-messages/` when source changes affect structured output, message parts, multimodal inputs, history serialization, or UI message contracts.
- Use `../models-and-providers/` for provider/model/profile/native-tool changes, optional provider extras, provider-specific VCR cassettes, and embedding behavior.
- Use `../cli-and-apps/` for `clai`, `pai`, web UI, custom agent loading, help-output tests, and example-application scaffolds.
- Use the root `pydantic-ai` provenance and refresh guidance when repository source, docs, examples, package metadata, or generated skill routing changes.

## Operating Rules

- Start with issue or PR context, maintainer alignment, and the narrowest reproducible problem; do not widen a bug fix based on hunches.
- Treat public API, docs, abstractions, tests, and generated agent skills as part of the product; prefer strong primitives over one-off flags or narrow batteries.
- Keep changes backward compatible for V1 unless the target is an explicitly beta surface or a documented major-version cleanup.
- Use targeted validation while iterating; reserve full `make` or full test/typecheck runs for final gates or when scope truly demands them.
- Prefer public-API integration tests with cassettes or snapshots for behavior users experience, and use unit tests only when they prove internal contracts cassettes cannot protect.
- Never record provider cassettes, run live paid requests, mutate cloud resources, or scrub cassette files without explicit user approval and a clear review plan.
- Update affected public docs, docstrings, examples, generated skills, and local workflow skills in the same change when mechanics or maintainer workflows change.
