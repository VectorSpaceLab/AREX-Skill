---
name: reinvent4
description: "Use REINVENT4 for molecular design CLI workflows: sampling,
  scoring, transfer learning, staged reinforcement learning, enumeration,
  plugins, and SMILES preprocessing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# REINVENT4

Use this repo skill when a task mentions REINVENT4, `reinvent`, `reinvent_datapre`, de novo molecular design, molecular scoring, transfer learning, staged reinforcement learning, peptide enumeration, LibInvent, LinkInvent, Mol2Mol, PepInvent, or REINVENT scoring plugins.

## First Checks

1. Confirm the package imports and CLIs are available:
   ```bash
   python scripts/check_reinvent_install.py
   ```
2. Read `references/cli-reference.md` when choosing global CLI flags, config formats, logging, seed handling, device overrides, or data-preprocessing CLI syntax.
3. Read `references/troubleshooting.md` when install/import, Torch/RDKit, CUDA/CPU, optional extras, config parsing, or missing dependency failures appear.
4. Read `references/repo-provenance.md` before deciding whether this skill matches a current checkout or needs refresh.

## Route By Task

- `sub-skills/sampling/SKILL.md`: sample or generate molecules from priors, TL/RL models, LibInvent scaffolds, LinkInvent warheads, Mol2Mol seeds, or PepInvent inputs.
- `sub-skills/scoring/SKILL.md`: build scoring-only configs, scoring blocks for RL, transforms, aggregation, custom `comp_*` plugins, and optional scoring integrations.
- `sub-skills/learning/SKILL.md`: configure transfer learning, staged RL/curriculum learning, diversity filters, inception memory, TensorBoard outputs, checkpoints, and TL-to-RL workflows.
- `sub-skills/data-pipeline/SKILL.md`: clean and filter SMILES datasets with `reinvent_datapre`, validate `data_pipeline.toml`, and create tiny preprocessing fixtures.
- `sub-skills/enumeration/SKILL.md`: configure peptide/library enumeration and validate scaffold, warhead, Mol2Mol, PepInvent, and amino-acid-library seed files.

## Install And Import Guidance

- Use Python 3.11 or newer, matching the package metadata requirement.
- For REINVENT4 CLI use, install the base package and a PyTorch wheel matching the host backend. Use CPU wheels for portable inspection and smoke checks; use CUDA/ROCm/XPU/MPS wheels only when the host driver/backend is known to support them.
- Optional extras are not needed for normal scoring/sampling/TL/RL config work unless the selected scoring component requires them:
  - `chemprop1` or `chemprop2` for ChemProp scoring components.
  - `openeye` for ROCS/OpenEye scoring, which also requires a valid license and package index.
  - `isim` for iSIM similarity tracking.
- At this repository snapshot, `reinvent --help` imports plotting code that requires `scipy`; install `scipy` if the CLI fails with `ModuleNotFoundError: No module named 'scipy'`.

## Common Command Shapes

```bash
reinvent --help
reinvent --device cpu --seed 123 --log-filename run.log config.toml
reinvent -f json --device cpu config.json
reinvent_datapre data_pipeline.toml --log-filename datapre.log
```

Convert configs without relying on source checkout helpers:

```bash
python scripts/convert_config_format.py input.toml output.json
python scripts/convert_config_format.py input.json output.yaml --output-format yaml
```

## Safe Operating Rules

- Validate configs and seed files with bundled scripts before launching expensive sampling, TL, RL, enumeration, or external scoring jobs.
- Run tiny CPU smoke checks before scaling to GPU or long jobs.
- Do not run workflows that require proprietary licenses, external services, model downloads, network calls, or long training unless the user explicitly approves those side effects.
- Keep REINVENT run configs, input SMILES, output CSV/model/checkpoint paths, and TensorBoard log directories explicit and separate per experiment.
