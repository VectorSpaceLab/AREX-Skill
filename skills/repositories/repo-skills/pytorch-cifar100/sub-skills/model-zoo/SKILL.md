---
name: model-zoo
description: "Select and instantiate CIFAR-100 CNN architectures for this repo."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Model Zoo

Use this sub-skill to choose a supported CIFAR-100 architecture, map the exact `-net` token to the right factory, and sanity-check that a checkout still returns 100-class logits from `32×32` inputs.

## Quick route

- Need the token → module/factory map? Read `references/model-catalog.md`.
- Need the `utils.get_network` contract, shapes, or size hints? Read `references/api-reference.md`.
- Need to diagnose unsupported names or import failures? Read `references/troubleshooting.md`.
- Need a fast checkout smoke test? Run `scripts/model_smoke.py`.
- Need training commands, warmup, TensorBoard, or checkpoints? Go to `../training/`.
- Need checkpoint loading, top-1/top-5 error reporting, or weight validation? Go to `../evaluation/`.

## Typical flow

1. Pick a token from the catalog.
2. Smoke the checkout with `scripts/model_smoke.py --repo-root <checkout> --net <name>`.
3. If the model passes, hand off to `../training/` or `../evaluation/` as needed.

## What stays here

- architecture selection
- token-to-factory routing
- input/output shape validation
- model import troubleshooting
- parameter-count guidance
