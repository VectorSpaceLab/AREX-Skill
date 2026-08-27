---
name: advanced-training
description: "Plan TotalSegmentator nnU-Net retraining, evaluation, dataset
  conversion, and model contribution workflows safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Advanced Training

Use this sub-skill only when a user explicitly asks about retraining, evaluating, contributing, or maintaining TotalSegmentator-style nnU-Net models. Ordinary users who just need masks should use [`../segmentation-workflows/SKILL.md`](../segmentation-workflows/SKILL.md) instead.

## Start Here

1. Confirm the request is research/maintenance work, not routine segmentation. Training and benchmark evaluation assume curated labels, nnU-Net v2, substantial storage, GPU memory, and multi-day runtime.
2. For retraining on the public CT TotalSegmentator dataset, follow [`references/training-and-evaluation.md`](references/training-and-evaluation.md): convert the dataset into nnU-Net layout, preprocess, train, predict the held-out split, then evaluate.
3. For a new anatomy or contributed model, first define the target modality, label set, dataset license, annotation quality, validation split, and whether the model is intended for upstream inclusion.
4. Treat release publishing, weight anonymization, server deployment, and package ownership steps as maintainer-only boundaries; do not run them unless the user is an authorized maintainer and explicitly asks.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) before launching expensive work so missing nnU-Net paths, class-map mismatches, benchmark-data assumptions, and GPU/runtime issues are caught early.

## Local References

- [`references/training-and-evaluation.md`](references/training-and-evaluation.md) covers dataset conversion contracts, nnU-Net command patterns, evaluation metrics, expected-result interpretation, model contribution boundaries, and package-management boundaries.
- [`references/troubleshooting.md`](references/troubleshooting.md) maps common training/evaluation failures to checks, recovery steps, and sibling-skill routes.

## Route Elsewhere

- Use [`../segmentation-workflows/SKILL.md`](../segmentation-workflows/SKILL.md) for `TotalSegmentator -i ... -o ...`, `python_api.totalsegmentator(...)`, speed modes, ROI subsets, and reports.
- Use [`../capability-discovery/SKILL.md`](../capability-discovery/SKILL.md) for supported runtime tasks/classes and `totalseg_info` discovery.
- Use [`../runtime-configuration/SKILL.md`](../runtime-configuration/SKILL.md) for installation, model weights, devices, licenses, offline caches, and telemetry configuration.
- Use [`../outputs-and-statistics/SKILL.md`](../outputs-and-statistics/SKILL.md) for run reports, segmentation statistics, multilabel outputs, probabilities, and mask combination.

## Safety Rules

- Do not present training as a default way to use TotalSegmentator; inference with released weights is the normal path.
- Do not copy or launch heavyweight training/evaluation scripts blindly; adapt the reference contracts to the user’s dataset and compute budget.
- Do not promise exact reproduction of released TotalSegmentator v2 results from the public dataset: the released v2 models used additional non-public data, and public images have blurred faces.
- Do not publish packages, tags, or model weights, and do not anonymize or upload weights, unless the user explicitly owns that release process.
