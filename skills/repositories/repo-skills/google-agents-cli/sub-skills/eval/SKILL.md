---
name: eval
description: "Use this sub-skill when designing, generating, grading, analyzing,
  comparing, or optimizing Agents CLI evaluation datasets and metrics for ADK
  agents."
metadata:
  disco-role: operating
  author: Google
  license: Apache-2.0
  version: 1.3.1
  requires:
    bins:
      - agents-cli
    install: "uv tool install google-agents-cli"
disable-model-invocation: true
license: Apache 2.0
---

# Evaluation Workflows

Use this sub-skill inside the `google-agents-cli` repo skill. It is a router plus operating checklist; move into the bundled references for full command flags, schemas, and examples.

## When to Use

- The user wants to create datasets, run inference traces, grade, analyze, compare, or optimize agent behavior.
- The task mentions `tests/eval`, `eval_config.yaml`, metrics, LLM-as-judge, user simulation, or multimodal eval.
- You need quality checks that are more robust than brittle pytest over model text.

## Workflow

1. Define the task-specific success criteria and dataset schema.
2. Generate traces, grade with suitable metrics, then analyze/compare results.
3. Use LLM-as-judge and user simulation only with explicit schemas and review.
4. Feed failures back into agent code or prompts; repeat the eval-fix loop.

## Read These References

- `references/eval-guide.md` — read for eval guide details.
- `references/builtin-tools-eval.md` — read for builtin tools eval details.
- `references/dataset_schema.md` — read for dataset_schema details.
- `references/metrics-guide.md` — read for metrics guide details.
- `references/multimodal-eval.md` — read for multimodal eval details.
- `references/user-simulation.md` — read for user simulation details.

## Verification and Safety

Safe checks: validate dataset/config shape and run help/parser checks; real `eval generate`/`grade` may call models and needs budget.

## Boundaries

- Does not author arbitrary agent code except as a feedback target.
- Does not run cloud-side evals or judge models without credentials/budget approval.

## Related Sub-Skills

- `../workflow/SKILL.md` — lifecycle routing and approval gates.
- `../scaffold/SKILL.md` — project creation/enhancement.
- `../adk-code/SKILL.md` — ADK Python implementation patterns.
- `../eval/SKILL.md` — evaluation loops and metrics.
- `../deploy/SKILL.md` — deployment and infrastructure.
- `../publish/SKILL.md` — Gemini Enterprise registration.
- `../observability/SKILL.md` — logging, tracing, and analytics.
