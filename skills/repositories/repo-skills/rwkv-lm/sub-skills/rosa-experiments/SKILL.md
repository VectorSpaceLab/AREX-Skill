---
name: rosa-experiments
description: "Guides RWKV-8 ROSA experimental scripts, suffix-automaton toy
  tasks, reverse-digit demos, and safe interpretation of GPU-heavy prototypes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RWKV-8 and ROSA experiments

Use this route when a request mentions RWKV-8, Heron, ROSA, Rapid Online Suffix
Automaton, 1-bit/4-bit ROSA, ROSA-QKV, reverse-digit toy tasks, or the small
experimental scripts under the RWKV-8 family.

## Route by task

- **Understand the idea**: read [rosa-workflows.md](references/rosa-workflows.md)
  for the suffix-automaton behavior and the purpose of each toy script family.
- **Run a CPU-safe toy check**: use
  [rosa_suffix_automaton_demo.py](scripts/rosa_suffix_automaton_demo.py) to see
  the core sequence behavior without training or checkpoints.
- **Debug a toy script**: read [troubleshooting.md](references/troubleshooting.md)
  before allocating GPU time or compiling CUDA kernels.

## What this route owns

- `RWKV-8.md` and `RWKV-v8/README.md` conceptual material.
- ROSA 1-bit and 4-bit language-model toy scripts.
- ROSA-QKV arithmetic and reverse-digit demos.
- Warnings about GPU, checkpoint, and runtime assumptions in experimental code.

## What this route does not own

- RWKV-7 production training belongs to `training-data`.
- Running a language-model checkpoint belongs to `inference-evaluation`.
- Tensor comparisons and checkpoint export belong to `architecture-reference`.

## Safe-use rule

Treat these scripts as research prototypes. They can be highly useful for
understanding suffix-state ideas, but most original scripts assume CUDA,
pre-existing `.pth` files, or long training loops. Do a CPU-safe algorithm check
first, then decide whether the full toy experiment is justified.
