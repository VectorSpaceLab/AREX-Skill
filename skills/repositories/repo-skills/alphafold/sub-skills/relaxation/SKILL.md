---
name: relaxation
description: "Guide AlphaFold Amber/OpenMM relaxation, AmberRelaxation APIs,
  CPU/GPU relax choices, structural violation metrics, and PDB cleanup
  constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AlphaFold Relaxation

Use this sub-skill when a task is about AlphaFold's Amber/OpenMM relaxation step, `AmberRelaxation`, `amber_minimize.run_pipeline`, CPU versus GPU relaxation, PDBFixer/OpenMM cleanup failures, or structural violation metrics reported by relaxation.

## Start Here

- Read [`references/workflows.md`](references/workflows.md) to decide whether to relax, how CLI relaxation maps to API calls, and when to switch GPU relaxation to CPU.
- Read [`references/api-reference.md`](references/api-reference.md) for `AmberRelaxation`, `amber_minimize`, cleanup helpers, debug data, and violation metric contracts.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for OpenMM platform errors, missing PDBFixer, poor residue definitions, atom-mask mismatches, repeated minimization failures, unstable GPU relaxation, and `models_to_relax=none` tradeoffs.
- Run [`scripts/check_relaxation_inputs.py`](scripts/check_relaxation_inputs.py) on a candidate PDB to inspect ATOM records, residue coverage, single-residue chains, common backbone gaps, heterogens, and optional OpenMM/PDBFixer import availability without running minimization.

## Routing Boundaries

- Use this sub-skill for `alphafold.relax.relax.AmberRelaxation`, `alphafold.relax.amber_minimize`, `alphafold.relax.cleanup`, `alphafold.relax.utils`, OpenMM/PDBFixer relaxation backend behavior, and structural violation metrics.
- Use `../prediction-cli/` for choosing top-level `--models_to_relax`, constructing `run_alphafold` commands, MSA reuse, model/database presets, and output-directory orchestration.
- Use `../outputs-and-confidence/` for interpreting `relaxed_*.pdb`, `unrelaxed_*.pdb`, `ranked_*.pdb`, `relax_metrics.json`, pLDDT, PAE, pTM, ipTM, AFDB, or AlphaFold Server outputs after files exist.
- Use `../model-config-and-api/` and the root troubleshooting guidance for shared package/backend conflicts involving JAX, OpenMM, CUDA, TensorFlow, NumPy, or installed dependency pins.

## Safe Operating Rules

- Do not run Amber relaxation, OpenMM minimization, or full AlphaFold prediction during routine validation; relaxation can require working OpenMM platforms and can be slow or hardware-sensitive.
- Treat `--models_to_relax=none` as a valid troubleshooting or exploratory choice when OpenMM/PDBFixer is failing; explain that structures may retain distracting stereochemical violations.
- Prefer CPU relaxation for stability triage when CUDA/OpenMM errors, GPU nondeterminism, or GPU platform availability is the suspected blocker; warn that CPU relaxation is usually slower.
- Treat relaxation as a stereochemical cleanup step, not a confidence-improvement step. It should not change pLDDT/PAE interpretation, and output confidence routing belongs in `../outputs-and-confidence/`.
- Keep public guidance environment-neutral: use package APIs and user-owned paths, not local inspection environment paths or source-checkout-only fixtures.

## Bundled Helper

```bash
python sub-skills/relaxation/scripts/check_relaxation_inputs.py ranked_0.pdb --check-imports --json
```

The helper is standalone, uses only the Python standard library by default, and never imports AlphaFold, runs PDBFixer cleanup, creates an OpenMM system, or performs minimization.
