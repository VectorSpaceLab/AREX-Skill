---
name: paws-x
description: "Routes LibMTL's PAWS-X multilingual text benchmark workflow."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# paws-x

Use this sub-skill for the PAWS-X / XTREME multilingual sentence
classification workflow.

## Covers

- PAWS-X training and evaluation.
- The multilingual tokenizer and cached feature pipeline.
- The raw TSV data layout and cache naming convention.
- Compatibility issues around `transformers`, `AdamW`, and the legacy raw
  preprocessing helpers.

## Does not cover

- Vision, Office, or QM9 benchmarks.
- Core trainer internals unless the question is specifically about the text
  workflow wiring.
- Raw data download automation as a runtime action; treat that as reference-
  only because it depends on external network access.

## When to use this sub-skill

Choose this route when the user asks things like:

- "How do I run PAWS-X?"
- "Where do the cached features come from?"
- "Why does the multilingual example need `AdamW`?"
- "What TSV files are expected for the text workflow?"
- "How do I handle the raw preprocess helpers?"

## Read next

- `../../references/configuration.md` for the shared flags and trainer kwargs.
- `../../references/troubleshooting.md` for cross-cutting install and runtime
  failures.
- `references/workflows.md` for the benchmark recipe.
- `references/task-contracts.md` for the language tasks, cache format,
  tokenizer, and decoder contract.
- `references/data-layouts.md` for the TSV and cache layout.
- `references/troubleshooting.md` for PAWS-X-specific failures.

## Workflow

1. Confirm the dataset root and the `pawsx` subdirectory.
2. Run `scripts/check_pawsx_data.py` to confirm the TSV tree, cache naming,
   and `transformers.AdamW` compatibility.
3. Confirm the cache or tokenizer download strategy before training.
4. Keep the example on a CUDA-capable runtime.

## Critical constraints

- The benchmark uses English, Chinese, German, and Spanish.
- The loader caches tokenized features on disk.
- The example is multi-input and uses the shared LibMTL trainer.
- The raw preprocess helpers are legacy-sensitive and should be treated as
  reference material unless the environment is explicitly prepared for them.

## Exit criteria

Leave this sub-skill when the user has the data tree, cache story, and runtime
compatibility notes for the multilingual benchmark.
