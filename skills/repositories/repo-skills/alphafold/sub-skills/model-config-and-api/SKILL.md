---
name: model-config-and-api
description: "Inspect and modify AlphaFold model presets, RunModel
  configuration, feature processing, parameter loading, and backend dependency
  issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlphaFold Model Config and API

Use this sub-skill when a task is about AlphaFold's programmatic model layer: choosing model presets, inspecting or editing `ml_collections` configs, constructing `RunModel` objects, processing model features, loading Haiku parameters, diagnosing JAX/Haiku/TensorFlow imports, or using model-side geometry and lDDT helper APIs.

## Start Here

- Run [`scripts/inspect_model_presets.py`](scripts/inspect_model_presets.py) to list installed model presets and selected configuration fields without loading weights or running inference.
- Read [`references/model-overview.md`](references/model-overview.md) for preset selection, config-editing patterns, RunModel lifecycle, dependency roles, and weight compatibility rules.
- Read [`references/api-reference.md`](references/api-reference.md) for model config APIs, `RunModel`, parameter loading, feature processing, and numerical helper contracts.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for import failures, JAX/JAXLIB mismatch, parameter path mismatches, TensorFlow/NumPy pin conflicts, GPU memory caveats, and preset/weight confusion.

## Routing Boundaries

- Use this sub-skill for `alphafold.model.config`, `alphafold.model.model.RunModel`, `alphafold.model.data.get_model_haiku_params`, `alphafold.model.features`, model geometry helpers, lDDT/FAPE helpers, and dependency/backend diagnostics.
- Use `../prediction-cli/` for building `run_alphafold` commands, CLI flags, database path flags, MSA reuse, random seeds, and output-directory orchestration.
- Use `../outputs-and-confidence/` for interpreting `ranking_debug.json`, `confidence_*.json`, `pae_*.json`, pLDDT, PAE, pTM, ipTM, PDB, mmCIF, AFDB, or AlphaFold Server JSON outputs.
- Use `../relaxation/` for Amber/OpenMM relaxation configuration, stereochemical cleanup, GPU relaxation, and relaxation failure modes.
- Use `../input-data-and-formats/` for FASTA/MSA/template parsing and data-pipeline input formats before model feature processing.

## Safe Operating Rules

- Do not load model weights, instantiate expensive model runners, call `RunModel.predict`, or run JAX compilation as a routine validation step.
- Treat `model_config()` inspection as safe; treat `RunModel` construction and feature processing as dependency-sensitive because JAX, Haiku, and TensorFlow may import or initialize runtime backends.
- Keep model names and parameter files aligned: `model_1_ptm` expects `params_model_1_ptm.npz`, while multimer v3 preset names expect `params_model_1_multimer_v3.npz` through `params_model_5_multimer_v3.npz`.
- Prefer explicit preset selection over manual ad hoc config edits, then make small config changes with `with cfg.unlocked()` or `with dataclass_cfg.unfreeze()` only when the task truly needs them.

## Bundled Helper

```bash
python sub-skills/model-config-and-api/scripts/inspect_model_presets.py --json
```

The helper imports only `alphafold.model.config`, reads installed package metadata when available, prints preset/config summaries, and never opens parameter files or runs inference.
