---
name: experimental
description: "Routes unstable cleanlab experimental helpers for low-memory
  batched label finding, span labels, and optional PyTorch examples."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# cleanlab experimental helpers

Use this sub-skill only when the user explicitly wants `cleanlab.experimental` behavior or accepts an unstable helper because the stable route does not fit their constraint. The cleanlab experimental docs warn that these methods are bleeding edge, may have sharp edges, and are not guaranteed stable across cleanlab versions.

## Route here

- `cleanlab.experimental.label_issues_batched.find_label_issues_batched` or `LabelInspector` for very large multiclass `labels` / `pred_probs` where normal in-memory label-issue detection is too memory hungry.
- `cleanlab.experimental.span_classification` when the user specifically asks for the experimental span-label wrapper around token classification.
- `cleanlab.experimental.mnist_pytorch`, `cleanlab.experimental.cifar_cnn`, or `cleanlab.experimental.coteaching` when the user wants the optional PyTorch/CIFAR/MNIST/co-teaching examples and accepts extra dependencies, training cost, and instability.
- Opt-in smoke validation with [`scripts/smoke_experimental.py`](scripts/smoke_experimental.py) before relying on these APIs in a fresh environment.

## Prefer stable sibling routes first

- Use [`../classification/SKILL.md`](../classification/SKILL.md) for standard `CleanLearning`, `filter.find_label_issues`, `count`, `rank`, dataset health, noisy-label benchmarking, and the core low-memory label-inspection idea when the user has not explicitly chosen the experimental batched helper.
- Use [`../structured-label-issues/SKILL.md`](../structured-label-issues/SKILL.md) for stable token-classification workflows. Route stable token-label issue detection there instead of using `experimental.span_classification`.
- Use [`../datalab/SKILL.md`](../datalab/SKILL.md), [`../multiannotator/SKILL.md`](../multiannotator/SKILL.md), [`../outlier/SKILL.md`](../outlier/SKILL.md), or [`../tabular-label-issues/SKILL.md`](../tabular-label-issues/SKILL.md) for their stable workflow families.

## Read these bundled references

- [`references/overview.md`](references/overview.md): task routes, minimal workflows, and the source-artifact bundling decision for this sub-skill.
- [`references/dependency-matrix.md`](references/dependency-matrix.md): required and optional dependencies, including `torch`, `torchvision`, and `skorch` boundaries.
- [`references/troubleshooting.md`](references/troubleshooting.md): missing optional packages, file-backed array mistakes, slow training/downloads, span wrapper limitations, and experimental deprecation risk.

## Operating cautions

- Do not describe these helpers as production-stable defaults or dependency-free.
- Do not make the PyTorch examples part of a stable cleanlab route; they are optional examples, not a required package path.
- For low-memory multiclass inspection, explain the stable classification workflow first, then mention `label_issues_batched` only when the user needs file-backed or multi-batch processing.
- For span data, state that `span_classification` is a thin wrapper over `cleanlab.token_classification`; use stable token-classification guidance for ordinary token-label tasks.
