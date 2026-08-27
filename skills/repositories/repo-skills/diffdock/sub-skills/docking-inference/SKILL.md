---
name: docking-inference
description: "Plan, validate, command-build, and troubleshoot DiffDock
  command-line docking prediction runs for single complexes or batch CSV
  inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Docking Inference

Use this sub-skill when a user wants to run, adapt, or debug DiffDock command-line docking prediction with `python -m inference`. It covers single-complex and batch CSV inputs, model/config choices, output layout, confidence-ranked SDF files, optional reverse-process visualization, and safe validation before expensive runs.

## Start Here

1. Check runtime prerequisites in [the root install/runtime reference](../../references/install-and-runtime.md) when that file is present, especially the Torch, PyG, RDKit, ProDy, ESM/OpenFold, and CUDA notes.
2. Pick the input mode in [input-output-formats.md](references/input-output-formats.md): batch CSV or single complex.
3. Build a dry command with [scripts/build_inference_command.py](scripts/build_inference_command.py); it prints a command and never runs inference.
4. Validate CSV or single-complex inputs with [scripts/validate_inference_inputs.py](scripts/validate_inference_inputs.py); it uses only Python standard-library modules.
5. Review [cli-reference.md](references/cli-reference.md), [configuration.md](references/configuration.md), and [troubleshooting.md](references/troubleshooting.md) before launching a long model run.

## Routes

- **Batch docking:** use a CSV with `complex_name`, `protein_path`, `ligand_description`, and `protein_sequence`; see [input-output-formats.md](references/input-output-formats.md).
- **Single-complex docking:** provide either `--protein_path` or `--protein_sequence`, plus `--ligand_description`; see [cli-reference.md](references/cli-reference.md).
- **Model/checkpoint overrides:** use `--model_dir`, `--confidence_model_dir`, `--ckpt`, and `--confidence_ckpt`; see [configuration.md](references/configuration.md).
- **Output inspection:** expect one output directory per complex and confidence-ranked SDF names; see [input-output-formats.md](references/input-output-formats.md).
- **Failure recovery:** diagnose imports, CPU/GPU behavior, model downloads, invalid inputs, RDKit parsing, ESMFold sequence paths, and GNINA caveats in [troubleshooting.md](references/troubleshooting.md).

## Boundaries

- For the graphical Gradio wrapper and browser UI, route to [web-ui](../web-ui/SKILL.md).
- For benchmark metrics, aggregate RMSD reporting, and evaluation datasets, route to [evaluation-benchmarks](../evaluation-benchmarks/SKILL.md).
- For training, dataset preparation, and ESM embedding preparation for evaluation/training, route to [training-data](../training-data/SKILL.md).
- This sub-skill does not run DiffDock, download models, import heavy DiffDock modules, or require the original repository examples to remain available.
