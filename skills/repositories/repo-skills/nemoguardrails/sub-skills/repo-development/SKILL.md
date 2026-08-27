---
name: repo-development
description: "Use for source-checkout contribution and maintainer work in NVIDIA
  NeMo Guardrails: policy gates, public API/provider invariants, focused tests,
  pre-commit, docs validation, generated-file rules, and review readiness."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# repo-development

Use this sub-skill only when the user is working in a live NVIDIA NeMo Guardrails source checkout or is preparing contribution/maintenance guidance for that checkout.

## Route here

- The user wants to modify repository source, tests, docs, packaging, provider integrations, server behavior, tracing, telemetry, or public APIs.
- The user asks which validation commands to run before handoff or PR readiness.
- The user asks about issue/PR policy, DCO, AI-assisted contribution disclosure, changelog rules, generated files, or review readiness.
- The user asks to add or change an LLM provider, embedding provider, optional rail, HTTP client path, server API shape, tracing/telemetry behavior, or source-checkout test.

## Route away

- Installation, import checks, package extras, or CLI discovery with no source edit: use `setup-and-basics`.
- Guardrails config, Colang, custom actions, catalog rails, or config validation with no source edit: use `configure-rails`.
- Python API, CLI chat/server, OpenAI-compatible endpoints, streaming, or integrations with no source edit: use `run-rails`.
- Evaluation, logging, tracing, metrics, or telemetry usage with no source edit: use `evaluate-and-observe`.
- Direct branch push, PR opening, or PR submission: stop at draft text unless the user explicitly directs the action and the repository policy checks in [contributor-workflow](references/contributor-workflow.md) pass.

## Operating procedure

1. Confirm you are in a live source checkout before recommending checkout commands. Installed-package users cannot run this repository's `make test`, `make pre-commit`, or docs build targets unless they have cloned the repository and installed development dependencies.
2. For contribution policy, issue/PR gatekeeping, DCO, AI disclosure, duplicate-work checks, and review readiness, use [contributor-workflow](references/contributor-workflow.md).
3. For local setup, focused tests, `make` targets, pre-commit, docs validation, fake-model testing, and no-live-provider safety, use [test-and-validation](references/test-and-validation.md).
4. For code changes under the runtime package, especially providers or public APIs, use [provider-integration-rules](references/provider-integration-rules.md) before editing.
5. For docs, generated SDK references, snapshots, changelogs, notebooks, and maintainer-only scripts, use [docs-and-generated-files](references/docs-and-generated-files.md).
6. When validation or policy checks fail, consult [troubleshooting](references/troubleshooting.md) and report what was run, what was skipped, and any residual risk. Do not fabricate GitHub assignment, review, CI, benchmark, or compatibility results.

## Minimum answer shape for source changes

- State the intended scope and whether it is a source-checkout task.
- Name the policy gates that apply before branch push or PR submission.
- Describe the implementation path while preserving public API, sync/async, optional dependency, secret-handling, logging, and observability invariants.
- Select focused tests first; broaden only when shared behavior, public APIs, packaging, docs, server, tracing, or generation paths are affected.
- End with validation status, skipped checks, and PR/draft handoff status.
