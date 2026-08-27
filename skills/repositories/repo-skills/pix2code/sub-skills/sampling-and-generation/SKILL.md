---
name: sampling-and-generation
description: "Validate pix2code trained artifacts and generate DSL from
  screenshots using greedy or beam search workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sampling and Generation

Use this sub-skill when the user wants to turn one screenshot or a directory of screenshots into pix2code DSL output, or when they need to check that a trained artifact directory is complete before sampling.

## Read first

- [references/artifact-contract.md](references/artifact-contract.md) for the required files inside a trained model directory.
- [references/inference-workflows.md](references/inference-workflows.md) for greedy versus beam search usage and the single-image versus batch scripts.
- [references/troubleshooting.md](references/troubleshooting.md) for missing weights, mismatched metadata, OpenCV preprocessing issues, and stale wrapper problems.
- [scripts/check_pix2code_artifacts.py](scripts/check_pix2code_artifacts.py) to validate a trained-artifact directory before any sampling command.

## Quick workflow

1. Verify the artifact directory first:

```bash
python sub-skills/sampling-and-generation/scripts/check_pix2code_artifacts.py --artifacts bin
```

2. Sample a single screenshot when the artifacts are complete by adapting the legacy argument order described in `inference-workflows.md`.

3. Sample a directory of screenshots when you want a batch of `.gui` outputs by using the same artifact-directory and search-mode conventions.

4. If the task is only to diagnose missing files or stale artifacts, use the bundled checker and stop there.

## Boundaries

This sub-skill owns artifact validation and screenshot-to-DSL generation guidance. It does not own dataset preparation; route that to [../data-and-training/SKILL.md](../data-and-training/SKILL.md). It does not own DSL compilation; route that to [../dsl-compilation/SKILL.md](../dsl-compilation/SKILL.md).

## Validation checklist

- The artifact directory contains `pix2code.json`, `pix2code.h5`, `meta_dataset.npy`, and `words.vocab`.
- `meta_dataset.npy` holds the input shape and output size expected by the sampler.
- The screenshot input exists and is readable by OpenCV.
- Greedy search is the default path; beam search is selected by passing an integer beam width.
- The generated DSL output is a `.gui` file with the original tokens stripped of `<START>` and `<END>`.
