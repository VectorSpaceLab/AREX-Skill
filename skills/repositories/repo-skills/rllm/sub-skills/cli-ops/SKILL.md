---
name: cli-ops
summary: "Operate rLLM setup, model/provider config, project scaffolds, agent
  registry, view, and snapshots."
description: "Use rLLM CLI operations for model/provider setup, UI login,
  project scaffolding, agent/evaluator registration, result viewing, and sandbox
  snapshot management."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# rLLM CLI Operations

Use this sub-skill for support commands around the core eval/data/training workflows: `rllm model`, `rllm login`, `rllm init`, `rllm agent`, `rllm view`, and `rllm snapshot`.

## Start Here

1. Read root `references/cli-command-map.md` to identify the command owner.
2. Read `references/workflows.md` for provider setup, scaffold/registry, viewing, and snapshot workflows.
3. Read `references/troubleshooting.md` for config, login, registry, viewer, and snapshot failures.
4. Switch to `../evaluation/SKILL.md`, `../datasets/SKILL.md`, or `../training/SKILL.md` when the task moves from setup into execution.

## Safe Check

```bash
python scripts/inspect_cli_state.py
```

The helper reads rLLM home config/registry files and prints a redacted summary. It does not modify state or validate remote credentials.

## Avoid

- Do not store raw API keys in generated examples, logs, or reports.
- Do not overwrite scaffold output directories unless the user explicitly accepts it.
- Do not build or destroy snapshots without confirming the target backend and benchmark slice.
