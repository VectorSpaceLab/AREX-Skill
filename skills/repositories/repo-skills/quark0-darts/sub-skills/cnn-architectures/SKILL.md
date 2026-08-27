---
name: cnn-architectures
description: "Plan and troubleshoot convolutional DARTS workflows for CIFAR-10
  and ImageNet."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# cnn-architectures

Use this sub-skill for convolutional DARTS questions: CIFAR-10 architecture search, CIFAR-10 training/evaluation from a genotype, ImageNet training/evaluation, pretrained CNN checkpoint evaluation, CNN cell/model API behavior, and CNN-specific runtime failures.

## Read order

- For commands, flags, outputs, expected metrics, and safe smoke checks, read [workflows](references/workflows.md).
- For source-backed architecture/API facts about search networks, fixed-genotype networks, operations, transforms, and checkpoint formats, read [api-reference](references/api-reference.md).
- For failure triage, legacy CUDA/PyTorch issues, data/checkpoint problems, OOM, nondeterminism, and augmentation/drop-path confusion, read [troubleshooting](references/troubleshooting.md).

## Routing boundaries

- Genotype catalogs, genotype schema editing, and DOT/Graphviz rendering details route to `../genotypes-and-visualization/`.
- Cross-cutting dataset, checkpoint download, and legacy runtime setup details route to the root references once available, especially `../../references/data-and-checkpoints.md`, `../../references/legacy-runtime.md`, and `../../references/troubleshooting.md`.
- Prefer the root command planner `../../scripts/darts_command_builder.py` when it is present. It should generate commands and prerequisites; do not copy or recreate long runner scripts in this sub-skill.

## Operating constraints

- Treat all CNN runner scripts as reference-only evidence. The DARTS project is script-style, not an installable Python package.
- Native CNN workflows are legacy CUDA workflows. Do not promise successful execution on modern Python/PyTorch or CPU-only hosts.
- Do not reopen the source tree for routine answers; the references in this sub-skill are intended to be sufficient for novice and expert CNN DARTS planning.
- When advising on full training or evaluation, distinguish architecture search validation from final architecture evaluation. Search validation accuracy is not the paper result.

## Evidence basis

This sub-skill distills the README CNN sections and the CNN source scripts/modules covering CIFAR/ImageNet runners, search and fixed-genotype networks, operations, architect updates, utilities, and genotype consumption. It intentionally excludes detailed genotype catalogs and visualization internals, which belong to the genotype/visualization sub-skill.
