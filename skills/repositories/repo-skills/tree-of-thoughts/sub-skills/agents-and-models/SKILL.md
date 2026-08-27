---
name: agents-and-models
description: "Configure and inspect tree-of-thoughts TotAgent model adapters,
  Thought output contracts, and safe model preflight checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# agents-and-models

Use this sub-skill when a task needs to configure, inspect, or preflight the `tree-of-thoughts` model-facing agent layer before using search workflows. It covers `TotAgent`, the `Thought` schema, OpenAI caller configuration, injected custom or fake models, model-output validation, and failure diagnosis.

## Route here for

- Verifying that `TotAgent` imports and that the installed dependency set is compatible.
- Choosing between the default OpenAI function caller and `use_openai_caller=False` with a custom or fake model runner.
- Validating that a model returns dict-like text with `thought` and numeric `evaluation` keys.
- Building deterministic fake agents for safe downstream DFS/BFS smoke checks without external services.
- Diagnosing import, API-key, parser, constructor side-effect, or no-PyTorch warnings around model setup.

## Do not handle here

- DFS/BFS traversal parameters, pruning behavior, breadth limits, or result interpretation. Route those to the search-workflows sub-skill.
- Stale maintainer scripts, packaging release automation, or project-wide cleanup. Route those to the root troubleshooting or maintainer references.

## Runtime references

1. Read [references/api-reference.md](references/api-reference.md) for verified signatures, install/import expectations, environment setup, model-output contracts, and safe fake/custom model examples.
2. Read [references/troubleshooting.md](references/troubleshooting.md) for concrete symptoms, causes, commands, and expected recovery signals.
3. Use [scripts/check_model_contract.py](scripts/check_model_contract.py) to validate sample model output before passing it into `TotAgent.run` or DFS/BFS wrappers.

## Operating guardrails

- Treat model output as trusted-only or tightly constrained: this package converts text to a dict with Python `eval`.
- Prefer deterministic fake/custom runners for CI, smoke tests, and offline checks; the default `TotAgent(use_openai_caller=True)` requires `OPENAI_API_KEY` and external OpenAI-compatible service access.
- Keep API keys out of prompts, logs, sample outputs, and generated files.
- Validate the model contract before debugging DFS/BFS behavior; traversal code assumes every generated thought is a dict with exact `thought` and `evaluation` keys.
