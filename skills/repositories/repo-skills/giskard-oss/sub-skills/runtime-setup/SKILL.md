---
name: runtime-setup
description: "Install, import, and diagnose the Giskard OSS split-package
  runtime and core utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Giskard Runtime Setup

Use this sub-skill when a task is about installing Giskard, choosing optional
extras, importing the v3 split packages, disabling telemetry, diagnosing package
namespace conflicts, or using the small utilities exported by `giskard.core`.

## Read First

- [API reference](references/api-reference.md) for package/import boundaries and
  `giskard.core` utility contracts.
- [Workflows](references/workflows.md) for install commands, telemetry opt-out,
  smoke checks, and core utility recipes.
- [Troubleshooting](references/troubleshooting.md) for common runtime failures.

## Typical Triggers

- "Install Giskard" or "Which `giskard[...]` extra do I need?"
- "Why does `import giskard_checks` fail?"
- "Why is `import giskard.core` reporting a legacy package conflict?"
- "Disable telemetry before running Giskard in this process."
- "Check installed Giskard package versions without making provider calls."
- "Use `MinIntervalRateLimiter`, `Discriminated`, or `Error`."

## Boundaries

Handle here:

- Python version and install command selection for the base distribution,
  `scan`, provider, LiteLLM, checks, and scanner extras.
- The v3 namespace layout: usable APIs are under `giskard.core`,
  `giskard.agents`, `giskard.llm`, `giskard.checks`, and `giskard.scan`.
- The root `giskard` meta-distribution/shim and legacy package conflict.
- Telemetry opt-out with `DO_NOT_TRACK`, `GISKARD_TELEMETRY_DISABLED`, and
  `disable_telemetry()`.
- `giskard.core` utilities: rate limiters, discriminated unions, serializable
  errors, version helpers, and telemetry context helpers.
- No-network import and version smoke checks.

Route elsewhere:

- Evaluation scenarios, suites, deterministic checks, judges, and JUnit export:
  [checks-evals](../checks-evals/SKILL.md).
- Provider aliases, model strings, completions, embeddings, responses, and SDK
  errors: [llm-providers](../llm-providers/SKILL.md).
- Chat workflows, tools, templates, structured output, and generator orchestration:
  [agents-workflows](../agents-workflows/SKILL.md).
- Vulnerability scans, quality scans, `KnowledgeBase`, scan generators, and
  third-party scanner integrations: [scan-redteam](../scan-redteam/SKILL.md).

## Operating Rule

Set telemetry opt-out environment variables before the first `giskard.*` import
when a user asks for privacy-first execution. Use installed-package imports and
self-contained smoke checks; do not depend on a source checkout being present.
