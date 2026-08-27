---
name: design-pipeline
description: "Install prerequisites, select BindCraft design and filter presets,
  construct a CUDA direct or SLURM launch, and operate or resume the AF2/MPNN
  validation campaign."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Run the BindCraft design pipeline

Use this route after [target-preparation](../target-preparation/SKILL.md) has
produced a target-settings JSON. It covers the long-running GPU campaign, not
PDB preprocessing or downstream binder selection. Use
[results-analysis](../results-analysis/SKILL.md) for output interpretation.

## Route

1. Establish a Python 3.10 environment with a CUDA-capable NVIDIA GPU, a
   compatible JAX/JAXLIB CUDA build, ColabDesign, PyRosetta, scientific Python
   dependencies, a readable AF2 parameter bundle (about 5.3 GB), and usable
   DSSP and DAlphaBall executables. PyRosetta licensing is a separate legal
   gate; commercial use requires the applicable license. Do not treat a CPU
   environment as a substitute for this pipeline.
2. Confirm that the target JSON has been validated and that `design_path` is
   writable. Select an advanced preset and a filter preset; copy/adapt JSONs
   rather than silently editing a shared preset. See
   [advanced-settings](references/advanced-settings.md) and
   [filter-settings](references/filter-settings.md).
3. Check the AF2 parameter directory, `dssp_path`, and `dalphaball_path` in the
   advanced settings. Empty paths are resolved by BindCraft's own defaults;
   verify those defaults on the installation being used rather than assuming a
   checkout-relative path.
4. Build a command without executing it:

   ```bash
   python skills/disco/bindcraft/sub-skills/design-pipeline/scripts/build_bindcraft_command.py \
     --mode direct --settings ./settings_target/my_target.json \
     --filters ./settings_filters/default_filters.json \
     --advanced ./settings_advanced/default_4stage_multimer.json --dry-run
   ```

   Use `--mode slurm` and scheduler resource overrides for a batch launch. The
   builder only prints a shell-safe command; it never submits or runs one.
5. Launch with either the exact direct or SLURM forms in
   [launching](references/launching.md). Keep one campaign per `design_path`;
   do not run concurrent processes against the same CSVs and output folders.
6. Monitor trajectory acceptance, `failure_csv.csv`, GPU memory, and disk
   growth. The loop stops when the requested accepted count is reached, when
   `max_trajectories` is reached, or when the enabled acceptance-rate monitor
   decides that the campaign is underperforming. It is target-dependent and
   may require hundreds or thousands of trajectories; a short smoke test is
   not evidence of useful binder generation.
7. To continue a campaign, relaunch with the same target `design_path` and
   compatible settings after checking the existing CSV/PDB state. BindCraft
   has no separate `--resume` flag: existing trajectory names and accepted
   files are used to avoid some duplicate work, while the loop can add new
   random trajectories. Preserve the settings/filters/advanced files used by
   the campaign.

Detailed stage gates and artifacts are in [pipeline](references/pipeline.md);
launch flags and scheduler resources are in [launching](references/launching.md);
failure recovery is in [troubleshooting](references/troubleshooting.md).

## Safety boundary

The design loop calls AF2 backpropagation, MPNN sampling, AF2 complex and
monomer prediction, PyRosetta relaxation, and structural scoring. It requires
CUDA and external weights and can run for hours or days. Do not promise CPU
execution, affinity, or a successful target-dependent outcome. Do not bundle an
installer or download helper here; installation and weight acquisition require
user-controlled network, license, storage, and environment decisions.
