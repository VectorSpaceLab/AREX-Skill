---
name: evaluation
summary: "Run rLLM evaluations and author AgentFlow/Evaluator protocols."
description: "Use rLLM evaluation APIs and CLI for AgentFlow/evaluator
  authoring, benchmark execution, harness selection, sandboxed eval, saved
  episodes, and result interpretation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# rLLM Evaluation

Use this sub-skill when the task involves `rllm eval`, `@rllm.rollout`, `@rllm.evaluator`, `AgentFlow`, `Evaluator`, built-in/custom harnesses, benchmark scoring, pass@k, saved episodes, or debugging an agent's interaction traces.

## Start Here

1. Read `references/agentflow-and-evaluator-api.md` before writing custom flows or evaluators. It captures current import locations and return-type contracts.
2. Read `references/evaluation-workflows.md` for CLI recipes, provider/model selection, pass@k, sandboxed tasks, saved episode files, and programmatic `run_dataset` usage.
3. Read `references/troubleshooting.md` for common protocol, verifier, sandbox, provider, and result-schema failures.
4. For data layout or dataset registry work, switch to `../datasets/SKILL.md`. For provider/model setup, switch to `../cli-ops/SKILL.md`. For training rollouts, switch to `../training/SKILL.md`.

## Core Decisions

- **Is the agent a simple Python function?** Use `@rllm.rollout` and return an `Episode`, `Trajectory`, or `None`. A `None` return is valid when gateway traces will fill steps later.
- **Does the evaluator score host-side or in a sandbox?** Host-side evaluators can be fixed with `--evaluator`; per-task/verifier metadata is used when task config declares sandbox or script/module verifiers.
- **Does the task need a sandbox?** rLLM joins the flow's `needs_env`, the evaluator/verifier kind, and task metadata/environment directories. Do not provision sandboxes for tasks with no consumer.
- **Is this eval-only or training data generation?** Eval-only paths can save episodes/results; training paths must preserve token IDs/logprobs and route through the training sub-skill.

## Safe Checks

Run the bundled protocol smoke test to verify decorators and evaluator coercion without a model call:

```bash
python scripts/agentflow_eval_smoke.py
```

It constructs a tiny `Task`, `AgentConfig`, `Trajectory`, and evaluator result; it does not call a provider or modify user state.

## Avoid

- Do not copy stale imports from old docs if they reference missing `rllm.sdk` modules.
- Do not hard-code provider calls in evaluator tests; keep provider selection at the CLI/config boundary.
- Do not use a host-side evaluator for tasks whose `dataset.toml`/`task.toml` expects sandbox-side tests unless you intentionally override that behavior.
