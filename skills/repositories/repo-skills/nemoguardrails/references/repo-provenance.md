# Repository Provenance

Schema: `disco.repo-provenance.v1`

This skill was distilled from the NVIDIA NeMo Guardrails repository and installed-package inspection evidence.

## Source revision

| Field | Value |
| --- | --- |
| Repository | NVIDIA-NeMo/Guardrails |
| Remote | `https://github.com/NVIDIA-NeMo/Guardrails.git` |
| Branch at capture | `develop` |
| Commit | `877f33102ef85e1b0c6ec0624bc7123a73de4794` |
| Describe | `877f331` |
| Package distribution | `nemoguardrails` |
| Package version | `0.24.0.dev0` |
| Python support | `>=3.10,<3.14` |
| Dirty state | Source checkout was clean outside generated `skills/` outputs; generated runtime and review artifacts were intentionally present under `skills/` during construction |
| Provenance capture date | 2026-08-14 |

## Evidence used

Relative source evidence paths included:

- `README.md`, `pyproject.toml`, `Makefile`, `pytest.ini`.
- `nemoguardrails/__init__.py`, package import helpers, public LLM/type definitions, testing helpers, CLI modules, server modules, Guardrails/IORails/LLMRails runtime modules, config loader modules, evaluation modules, tracing/logging/telemetry modules, and LangChain integration modules.
- Public documentation under `docs/configure-rails/`, `docs/run-rails/`, `docs/evaluation/`, `docs/observability/`, `docs/integration/`, `docs/reference/cli/`, `docs/troubleshooting.mdx`, and `docs/telemetry.mdx`.
- Representative example configs and scripts under `examples/bots/`, `examples/configs/`, and `examples/scripts/` as evidence only; live-provider examples were not copied as runnable helpers.
- Behavior tests under `tests/test_imports.py`, config tests, CLI/server tests, Guardrails runtime tests, evaluation tests, LangChain integration tests, telemetry tests, and recorded/offline helper tests.
- Source-checkout policy files: `AGENTS.md`, package-level agent instructions, docs agent instructions, `CONTRIBUTING.md`, and `AI_POLICY.md`.

## Verification boundaries

- Required backend coverage for this skill is CPU/any Python runtime only.
- No CUDA, ROCm, MPS, Docker, live LLM provider, NIM service, Google Cloud moderation, telemetry staging, or large model-download backend was required for the selected scope.
- Safe bundled scripts use public package APIs and deterministic local checks; they do not depend on the original source checkout remaining available.
- Live-provider, heavyweight notebook, benchmark, container deployment, external telemetry, and credentialed service workflows are documented as caveats or routed to explicit user-authorized work rather than verified by default.

## Staleness signals

Refresh or re-verify this skill when any of these change materially:

- Public package version, supported Python range, extras, or CLI command names.
- `Guardrails`, `LLMRails`, `RailsConfig`, server schemas/endpoints, `RunnableRails`, evaluation CLI, tracing/telemetry, or testing helper APIs.
- Colang 1.0/2.x compatibility, guardrail catalog flow names, prompt task requirements, or config validation error behavior.
- Source contribution policy, validation commands, docs tooling, generated-file rules, or AI/contribution policies.
