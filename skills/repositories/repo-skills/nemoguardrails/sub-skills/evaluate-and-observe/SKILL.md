---
name: evaluate-and-observe
description: "Evaluate guardrails configs and diagnose logging, tracing,
  metrics, and telemetry behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# evaluate-and-observe

Use this sub-skill when the task is about evaluating a configured NeMo Guardrails app, reviewing evaluation outputs, or diagnosing logging, tracing, metrics, and anonymous telemetry behavior.

## Route here for

- `nemoguardrails eval run`, `check-compliance`, `ui`, and `eval rail` commands.
- Topical, moderation, hallucination, and fact-checking evaluation workflows.
- Understanding result directories, judge output, compliance summaries, and UI review.
- Verbose/debug logging, `explain()`, structured generation logs, and trace/metric/telemetry troubleshooting.
- Distinguishing anonymous usage telemetry from request tracing and metrics.

## Route away

- Guardrail config authoring, YAML/Colang changes, custom actions, or provider definitions: use `../configure-rails/SKILL.md`.
- Chat/server execution, streaming requests, or API integration: use `../run-rails/SKILL.md`.
- Source-editing, repo tests, docs, or contribution policy: use `../repo-development/SKILL.md`.

## References

- `references/evaluation.md` — CLI map, input/output contracts, output files, judge and cache caveats, offline boundaries.
- `references/observability-and-telemetry.md` — logging, tracing, metrics, telemetry, privacy, and opt-out behavior.
- `references/troubleshooting.md` — common failures and safe recovery paths.
