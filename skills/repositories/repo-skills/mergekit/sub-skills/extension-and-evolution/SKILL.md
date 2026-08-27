---
name: extension-and-evolution
description: "Extend mergekit with custom merge methods and task graphs, or plan
  optional evolutionary merge searches with explicit dependency and evaluation
  gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# Extension and evolution route

Use this route for a custom merge method, a reusable task-graph component, or
`mergekit-evolve`. It is an extension/developer route, not the normal YAML
method-selection route.

## Route first

- Use [merge-configs](../merge-configs/SKILL.md) for ordinary merge YAML,
  registered method selection, parameters, tokenizer, and chat templates.
- Use [model-io-and-architecture](../model-io-and-architecture/SKILL.md) for
  model references, architecture conversion, tensor IO, devices, and memory.
- Use [specialized-workflows](../specialized-workflows/SKILL.md) for raw,
  MoE, multi-stage, LoRA, tokensurgeon, or layer-shuffle commands.

## Custom method procedure

1. Define the mathematical contract and required parameters before choosing the
   decorator/easy-define or class-based implementation.
2. Implement a tensor-local method that respects mergekit's task and device
   contract; register it under the exact YAML method name.
3. Check registration in a clean import, exercise a tiny tensor fixture, and
   add focused tests for defaults, parameter validation, dtype, and device.
4. Run the graph tests and a focused package test before using the method in a
   real model merge. Keep the source method self-contained and documented.

Read [custom-methods.md](references/custom-methods.md) for the API patterns and
[troubleshooting.md](references/troubleshooting.md) for signature, registry,
and task-graph failures.

## Evolution procedure

Treat `mergekit-evolve` as optional and expensive. Preflight the `evolve` extra,
CMA-ES, evaluation backend, model/task config, storage, GPUs, and credentials
before constructing a run. The inspected environment intentionally omits
`ray`, `cma`, `lm_eval`, `wandb`, and `vllm`; `mergekit-evolve --help` therefore
fails at import with a missing `cma` module. This is an explicit optional gate,
not a core mergekit import failure.

Read [evolution.md](references/evolution.md) only after the preflight. Never
start a networked evaluation, W&B run, Ray cluster, vLLM server, or long CMA-ES
search as a smoke test. Record seeds, max evaluations, output paths, evaluator,
and stop conditions.

## Safe helper

Run `python scripts/check_extension_registration.py --help` or the default
probe to inspect core registration without invoking optional evolution.
