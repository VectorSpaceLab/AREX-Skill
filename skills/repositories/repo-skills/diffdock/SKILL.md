---
name: diffdock
description: "Route DiffDock docking, web UI, training/data preparation, and
  benchmark evaluation tasks to focused repo-specific guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DiffDock

Use this repo skill when a user is working with DiffDock: diffusion-based small-molecule docking to protein structures, DiffDock-L inference, the Gradio UI, training/data preparation, or benchmark evaluation.

## Start Here

1. Read [install-and-runtime.md](references/install-and-runtime.md) for setup routes, dependency families, backend expectations, and safe preflight checks.
2. Use [scripts/check_runtime_environment.py](scripts/check_runtime_environment.py) to inspect a candidate runtime without launching docking, training, or benchmarks.
3. Route to the focused sub-skill below, then use its bundled references and helper scripts before running expensive commands.
4. Read [troubleshooting.md](references/troubleshooting.md) when failures involve imports, CUDA/Torch/PyG, RDKit/ProDy/ESM/OpenFold, model checkpoints, network downloads, data paths, or GNINA.
5. Check [repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout.

## Routes

- **Docking prediction:** Use [docking-inference](sub-skills/docking-inference/SKILL.md) for single-complex or batch CSV inference, input validation, command construction, model/config overrides, output files, and confidence-ranked poses.
- **Web interface:** Use [web-ui](sub-skills/web-ui/SKILL.md) for the Gradio app, single-complex UI inputs, launch/deploy issues, and downloaded output zip inspection.
- **Training and data:** Use [training-data](sub-skills/training-data/SKILL.md) for score/confidence model training plans, dataset layouts, split files, ESM embeddings, cache checks, and checkpoint compatibility.
- **Benchmarks and metrics:** Use [evaluation-benchmarks](sub-skills/evaluation-benchmarks/SKILL.md) for PDBBind, BindingMOAD/DockGen, PoseBusters evaluation, RMSD/confidence metrics, GNINA post-processing, and vendored `spyrmsd` checks.

## Repository Model

DiffDock is a script-style research repository rather than a package with console entry points. Future agents should use the bundled command builders to assemble commands, then run those commands only in a user-provided DiffDock runtime checkout or project context that contains the expected DiffDock modules, data, checkpoints, and dependencies.

The generated skill is self-contained for planning, validation, troubleshooting, and command construction. It does not bundle model weights, processed benchmark datasets, GNINA, ESM models, or the full DiffDock source tree.

## Safe Defaults

- Prefer PDB protein inputs over sequence folding for lightweight inference smoke tests.
- Use command builders and validators first; they do not import the heavy DiffDock runtime stack.
- Treat full inference, Gradio launch, ESM extraction, training, benchmark evaluation, GNINA, and model downloads as potentially long-running or network/backend dependent.
- Keep user data paths explicit; do not assume the original example or dataset paths exist.
- Preserve `model_parameters.yml` beside checkpoints when moving trained score or confidence models.

## Required References

- [install-and-runtime.md](references/install-and-runtime.md) covers setup, Docker/conda expectations, optional dependencies, and environment checks.
- [troubleshooting.md](references/troubleshooting.md) covers cross-cutting failure modes shared by sub-skills.
- [repo-routing-metadata.json](references/repo-routing-metadata.json) is consumed by DisCo's managed repo-skills-router during import.
- [repo-provenance.md](references/repo-provenance.md) records the source snapshot and evidence baseline.
