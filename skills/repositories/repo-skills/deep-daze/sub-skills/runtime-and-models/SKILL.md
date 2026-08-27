---
name: runtime-and-models
description: "Runtime, dependency, CLIP model, cache, backend, and inspection
  guidance for deep-daze."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# runtime-and-models

Use this sub-skill when the task is to validate or troubleshoot a `deep-daze`
runtime before any image generation, especially around installation identity,
imports, package data, CLIP model names, tokenizer behavior, checkpoint cache
behavior, and CPU/GPU availability.

## Owns

- Distribution/import identity: package distribution `deep-daze`, import module
  `deep_daze`, exports `DeepDaze` and `Imagine`, and console script `imagine`.
- Dependency expectations for import, tokenization, CLI startup, CLIP loading,
  and generation-time optimizer/network components.
- CLIP model registry and tokenizer facts, including default model
  `ViT-B/32`, model names, token context length, and bundled BPE vocabulary.
- Runtime device behavior: CUDA when available, CPU fallback otherwise, and the
  practical limits of CPU-only generation.
- Checkpoint cache/download/checksum behavior and safe preflight inspection.
- Cross-cutting runtime troubleshooting before handing off to workflow-specific
  CLI or Python API instructions.

## Start here

1. For a safe environment preflight that does **not** download CLIP checkpoints
   or generate images, run:

   ```bash
   python scripts/check_deep_daze_runtime.py
   ```

   Use `python scripts/check_deep_daze_runtime.py --help` for options.
2. Read [references/runtime-reference.md](references/runtime-reference.md) for
   runtime facts, model names, cache semantics, and backend expectations.
3. Read [references/troubleshooting.md](references/troubleshooting.md) for
   dependency, BPE vocabulary, checkpoint, network, JIT, CPU/GPU, and resource
   failure modes.

## Route elsewhere

- For prompt-to-image command-line recipes, flags, and generation workflows,
  use [../cli-workflows/SKILL.md](../cli-workflows/SKILL.md).
- For programmatic `Imagine`/`DeepDaze` construction and Python generation
  recipes, use [../python-api/SKILL.md](../python-api/SKILL.md).

## Do not use this as a generation smoke test

This sub-skill intentionally avoids `Imagine(...)`, `deep_daze.clip.load(...)`,
and `imagine ...` generation commands. Those actions can download large CLIP
checkpoints, perform expensive optimization, write output files, and require
interactive or display-related behavior. Use this sub-skill only to decide
whether the runtime is plausibly ready and what must be fixed before generation.
