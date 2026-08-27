---
name: "pfllib"
description: "Routes PFLlib tasks for dataset preparation, federated-learning
  experiments, and library extension."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PFLlib

Use this skill for PFLlib dataset generation, experiment execution, and code
extension tasks.

## Start here

1. Create or verify a Python 3.11 environment with the PFLlib runtime stack:
   PyTorch, torchvision, torchtext, cvxpy, NumPy < 2, and the scientific stack
   used by the repository.
2. Run `scripts/check_install.py --repo-root <checkout>` to confirm imports and
   CUDA availability.
3. Run `scripts/scan_registry.py --repo-root <checkout>` when you need a quick
   view of the supported dataset, model, and algorithm surface.
4. Pick the sub-skill that matches the task family below.

## Routes

### `data-preparation`

Use this route to generate or validate client-split datasets such as MNIST,
AG News, Amazon Review, HAR, and the other built-in scenario generators.
Read `sub-skills/data-preparation/SKILL.md` first.

### `experiments`

Use this route to launch FL runs, tune CLI flags, inspect results, or check
privacy/system-condition settings. Read `sub-skills/experiments/SKILL.md`
first.

### `extension`

Use this route when you need to add a new algorithm, dataset, model, or
optimizer to the repo. Read `sub-skills/extension/SKILL.md` first.

## Shared helpers

- `scripts/check_install.py` — run this first when the environment or CUDA
  stack is in doubt.
- `scripts/scan_registry.py` — use this to inspect the supported registry before
  editing or launching.

## Read these references

- `references/repo-provenance.md` when you need to compare the skill against a
  checkout or decide whether it should be refreshed.
- `references/troubleshooting.md` for cross-cutting install, import, CUDA,
  cvxpy, and working-directory problems.
- `references/repo-routing-metadata.json` for the router placement data used by
  the live repo-skills router.

## Notes

- This repository is script-driven rather than a packaged library; use the
  bundled check and launch helpers against a local checkout.
- If a dataset tree is missing, route to `data-preparation` before launching an
  experiment.
- If the task is to change the codebase, not just run it, route to
  `extension`.
