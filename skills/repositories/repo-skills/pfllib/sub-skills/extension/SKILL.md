---
name: "extension"
description: "Routes PFLlib code changes that add or update algorithms, models,
  optimizers, and dataset generators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Extension

Use this route when you need to change PFLlib itself rather than run an
existing benchmark.

## Use this when

- You want to add a new federated-learning algorithm, client, or server.
- You want to add a new dataset generator or preprocessing flow.
- You want to add a new model, optimizer, or registry entry.
- You need to verify that a new code path is wired into `main.py` correctly.

## Read these references

- `references/api-reference.md` for the Server/Client hooks and registry
  expectations.
- `references/workflows.md` for the step-by-step add-a-feature checklists.
- `references/troubleshooting.md` for registration, shape, and dependency
  mistakes.

## Run these helpers

- `scripts/scan_registry.py` from the root route to inspect the current dataset,
  model, and algorithm registry before you edit it.
- `scripts/check_install.py` from the root route if the new feature introduces a
  dependency like `cvxpy`, `torchtext`, or `torchvision`.

## What belongs here

Include code changes and documentation for:

- new `server*.py` / `client*.py` pairs
- new dataset generators under `dataset/`
- new model classes under the model registry
- new optimizer hooks
- registry edits in `system/main.py`
- any support code required to make the new feature selectable from the CLI

## What does not belong here

- Launching an already-registered experiment; route that to `experiments`.
- Generating or validating client-split datasets that already exist; route that
  to `data-preparation`.
- Long result-analysis tasks after the change is already wired; route that back
  to `experiments`.

## Common workflow

1. Inspect the current registry and the relevant base classes.
2. Implement the new code path.
3. Wire it into `main.py` or the dataset loader as needed.
4. Re-check the registry and run a tiny smoke path from the experiments route.
5. Only then consider larger validation or downstream benchmarking.
