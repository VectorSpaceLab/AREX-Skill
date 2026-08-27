---
name: evaluation-benchmarks
description: "Plan and troubleshoot DiffDock benchmark evaluation runs,
  RMSD/confidence metrics, GNINA post-processing, and vendored spyrmsd checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DiffDock Evaluation Benchmarks

Use this sub-skill when a task is about reproducing or diagnosing DiffDock benchmark evaluations rather than making ad-hoc docking predictions.

## Route Here For

- Building benchmark commands for PDBBind, BindingMOAD/DockGen, or PoseBusters with `python -m evaluate`.
- Checking required dataset, split, ESM embedding, score model, confidence model, sampling, and output flags before an expensive run.
- Explaining saved evaluation outputs such as `rmsds.npy`, `confidences.npy`, `centroid_distances.npy`, `gnina_metrics.pkl`, and printed success-rate metrics.
- Diagnosing symmetry-corrected RMSD, confidence re-ranking, GNINA minimization, cache, CUDA/CPU, and benchmark data-layout failures.
- Inspecting the vendored `spyrmsd` CLI availability without running a benchmark.

## Route Elsewhere

- For single-complex or CSV-driven docking prediction, use [docking-inference](../docking-inference/SKILL.md).
- For dataset preparation, ESM embedding generation, training inputs, or training runs, use [training-data](../training-data/SKILL.md).

## Workflow

1. Identify the benchmark family: PDBBind, DockGen/BindingMOAD, or PoseBusters.
2. Read [evaluation workflows](references/evaluation-workflows.md) for dataset layouts, required flags, and command patterns.
3. Use [build_evaluation_command.py](scripts/build_evaluation_command.py) to construct a safe `python -m evaluate` command; the helper prints only and never runs DiffDock.
4. Read [RMSD and metrics](references/rmsd-and-metrics.md) before interpreting arrays, confidence ordering, GNINA metrics, or symmetry-corrected RMSD results.
5. Use [troubleshooting](references/troubleshooting.md) for dependency, backend, dataset, split, ESM, GNINA, cache, OOM, and result interpretation failures.
6. Use [inspect_spyrmsd_cli.py](scripts/inspect_spyrmsd_cli.py) to check vendored `spyrmsd` availability or construct a reference RMSD CLI command.

## Safety Notes

- Benchmark evaluation imports a heavy optional stack including Torch, PyG, W&B, RDKit, model code, and dataset loaders; plan validation before running it.
- Full benchmark runs require prepared data, cached ESM embeddings, model checkpoints, and significant compute; classify native benchmark commands as expensive unless scoped with `--limit_complexes`.
- GNINA is an external executable invoked by DiffDock; verify the binary and receptor/ligand layout before enabling GNINA flags.
