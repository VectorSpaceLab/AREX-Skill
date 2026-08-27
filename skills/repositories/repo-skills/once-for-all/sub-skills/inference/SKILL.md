---
name: inference
description: "Routes Once-for-All model loading, subnet sampling, hub entry
  points, and ImageNet-style evaluation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Inference

Use this sub-skill when the user wants to load an OFA supernet, sample or fix an active subnet, inspect the hub entry points, or evaluate a specialized OFA model on ImageNet-style data.

## Triggers

Choose this route for requests like:

- "load an OFA supernet"
- "sample a subnet from the supernet"
- "evaluate a specialized OFA model"
- "use the hubconf models"
- "run or adapt `eval_ofa_net.py`"
- "run or adapt `eval_specialized_net.py`"

## Included workflows

- Constructing `ofa_net` supernets.
- Constructing `ofa_specialized` models.
- Sampling active subnets and extracting a stand-alone subnet.
- Running a lightweight forward smoke on CPU or CUDA.
- Evaluating a model on an ImageNet-style `ImageFolder` layout.
- Reading and using the repo's PyTorch Hub shortcuts.

## Excluded workflows

- Predictor-driven search. Route that to `sub-skills/search/`.
- Distributed training. It is intentionally out of scope for this generated skill.

## Read next

- `references/model-overview.md` for the supported supernet and specialized-model families.
- `references/api-reference.md` for verified constructors and subnet methods.
- `references/workflows.md` for end-to-end model-loading and evaluation recipes.
- `references/troubleshooting.md` for download, dataset-layout, and backend issues.

## Bundled helper

- `scripts/evaluate_ofa.py` — safe wrapper for model smoke, optional subnet sampling, and ImageNet-style evaluation.

## Typical flow

1. Identify the model family and whether the user needs a supernet or a specialized model.
2. Load the model with `ofa_net` or `ofa_specialized`.
3. For supernets, sample or fix the active subnet if needed.
4. Run the bundled helper for a smoke pass or a small ImageNet-style evaluation.
5. Use the workflow reference when the user needs benchmark-quality subnet evaluation or a published specialized-model id.

## Practical notes

- `ofa_net(..., pretrained=False)` is the fastest safe smoke.
- `ofa_specialized(...)` may still resolve public config files, and pretrained behavior can also fetch weights.
- Real specialized-model benchmarking is best on CUDA with an ImageNet validation split.
- If the user only needs a shape check, the bundled helper can run without a dataset.
