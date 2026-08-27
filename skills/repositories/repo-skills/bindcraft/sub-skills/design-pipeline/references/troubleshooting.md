# Design-pipeline troubleshooting

Diagnose the earliest failed gate and preserve the campaign log, JSONs, and
output directory before changing anything. Do not infer a biological result
from an infrastructure failure.

## Installation and import failures

Install in this order so that each gate is observable:

1. Start from the intended BindCraft checkout/version and create a dedicated
   Python 3.10 Conda or Mamba environment. The repository installer accepts
   `--pkg_manager <conda-or-mamba>` and `--cuda <compatible-version>`; it is a
   mutating, network-heavy convenience script, not a portable lockfile. Review
   it before running and supply a CUDA version compatible with the GPU/driver.
2. Install the scientific stack used by the source: NumPy below 2 in the
   checked-in installer, pandas, matplotlib, Biopython, SciPy, pdbfixer,
   seaborn, tqdm, ffmpeg/fsspec/py3Dmol, and the JAX ecosystem dependencies.
   Select a CUDA JAX/JAXLIB build plus required CUDA/cuDNN runtime packages;
   the CPU build cannot run BindCraft's entry point.
3. Install ColabDesign for the chosen BindCraft revision, then verify
   `import colabdesign`. Install PyRosetta from an authorized distribution and
   verify `import pyrosetta`. PyRosetta is license-sensitive: an import does
   not grant commercial-use rights, so resolve the applicable RosettaCommons
   license and version policy before distributing or using results.
4. Acquire the AF2 parameter bundle in a user-controlled step, verify its size
   and contents, and point `af_params_dir` at it. Install or expose compatible
   DSSP and DAlphaBall executables and set their paths. Do not reuse paths from
   another host.
5. Run `python -m pip check`, then import JAX, ColabDesign, PyRosetta, and the
   BindCraft package functions in the same activated environment that will
   launch the campaign. A syntax or JSON check is not an import check.

The repository installer performs environment creation, package installation,
network downloads, PyRosetta installation, AF2-weight acquisition, and
executable permission changes. This skill intentionally does not bundle or
auto-run it. If importing the entry point fails before `--help`, classify the
missing module or shared library first. Do not try CPU mode as a workaround:
the entry point deliberately terminates when no JAX GPU is visible.

## CUDA, JAX, and memory

1. Check the driver sees the GPU and that `jax.devices()` reports at least one
   CUDA device. Confirm a tiny JAX array operation, not only the device list.
2. Ensure the JAX/JAXLIB CUDA build, CUDA runtime, cuDNN, and driver are a
   compatible set. Do not infer compatibility from an installed `nvcc`; the
   wheel/runtime path may not need a system compiler.
3. For OOM, stop rather than repeatedly retrying a corrupted process. Trim the
   target, reduce binder length, reduce design/validation recycles or
   iterations, lower `num_seqs`, disable optional animations/plots, or choose a
   less memory-intensive algorithm. Change one factor and record it.
4. `use_multimer_design`, template masking, initial guesses, large targets,
   more AF2 recycles, and 5-model validation can materially increase memory or
   time. A 32 GB GPU is the README's local recommendation for larger complexes,
   not a hard guarantee; target-dependent requirements can be higher.
5. Clear stale processes/VRAM between launches. Do not run two trajectories or
   jobs against one output directory.

## ColabDesign, AF2 weights, and paths

- Confirm `af_params_dir` points to the directory ColabDesign expects and that
  the external AF2 bundle is complete. The README/installer describe roughly
  5.3 GB of weights and the known parameter file `params_model_5_ptm.npz` is a
  useful presence check. Presence alone does not prove all models load.
- An empty path is resolved by BindCraft's installation-context logic; verify
  it for the current install rather than copying a path from another machine.
  Never put a private environment or verification path into a portable JSON.
- If ColabDesign reports missing parameters, check permissions, free disk,
  and the model directory passed to both design and validation. Do not download
  weights from inside an automated recovery loop without explicit user
  approval.
- Colab uses a different initialization order and storage location from local
  execution. Treat it as an alternative CUDA workflow, not evidence that a
  local SLURM environment is configured.

## PyRosetta, DAlphaBall, and DSSP

- PyRosetta initialization includes the configured DAlphaBall path. A missing,
  non-executable, wrong-architecture, or inaccessible DAlphaBall executable can
  fail at startup or during interface scoring. Set `dalphaball_path` to a valid
  executable supplied for the current platform.
- Secondary-structure calculations require a usable DSSP executable. Set
  `dssp_path` explicitly when the default cannot be found.
- For either tool, check `test -r` and `test -x` in the launch environment and
  verify that the scheduler compute node sees the same path. If permissions are
  wrong, fix them in the user-controlled installation (for example with an
  administrator-approved `chmod +x`), not by embedding a binary in this skill.
- The checked-in utility files are architecture-specific assets and are not
  bundled here. A present file without executable permission is a known setup
  warning, not a successful Rosetta/DSSP verification.

## Low confidence, clashes, and contacts

- `Trajectory/Clashing` means the final hallucination CA clash gate fired. It
  is not the same as a post-relaxation `Relaxed_Clashes` filter failure.
- `Trajectory/LowConfidence` can mean final binder pLDDT below 0.70 or fewer
  than three detected interface contacts. For 4stage, inspect earlier
  `Trajectory_logits_pLDDT`, `Trajectory_softmax_pLDDT`, and
  `Trajectory_one-hot_pLDDT` failures in `failure_csv.csv`.
- Check target trimming, target chain/hotspot syntax, binder length range,
  design algorithm, helicity/contact weights, and template masking. If the
  target site is intentionally unspecified, AF2 may select a site, so do not
  diagnose an unexpected site as a parser error without checking the input.
- Changing weights or using a hard-target initial guess can rescue a specific
  target while adding bias. Validate a new campaign separately and preserve
  provenance.

## Filter rejection and acceptance monitoring

- Read `failure_csv.csv` and separate early AF2 columns from Rosetta/interface,
  RMSD, binder-alone, and composition conditions. The checked-in
  `no_filters.json` sets all 218 thresholds to null, including early AF2
  thresholds, but it does not disable trajectory confidence, clash, contact,
  duplicate-sequence, or missing-interface gates.
- Confirm that every filter uses the intended `higher` direction and that null
  means disabled. Check model-specific fields against the selected model role;
  a null model slot is not a failed prediction.
- If the monitor prints that acceptance is below `acceptance_rate`, it stops
  after `start_monitoring` rather than continuing indefinitely. This is a
  campaign-control signal, not proof of no binding. Increase sampling or
  adjust a justified setting only after examining which failure columns
  dominate. The source's ratio uses the run's trajectory counter and accepted
  counter, so record whether this is a fresh run or continuation.
- When accepted count reaches the target, the program ranks accepted rows by
  `Average_i_pTM` and copies ranked PDBs. Do not call this affinity ranking;
  experimental validation remains necessary.

## Resume and damaged output

BindCraft has no `--resume` switch. A deliberate continuation uses the same
`design_path` and the same campaign settings. Before restarting:

1. Stop any old process and snapshot the settings/filter/advanced JSONs and
   scheduler log.
2. Inspect `trajectory_stats.csv`, `mpnn_design_stats.csv`,
   `final_design_stats.csv`, `failure_csv.csv`, and the relaxed/accepted PDB
   counts. Check for zero-byte or half-written files.
3. Quarantine incomplete rows/files outside the campaign directory; do not edit
   CSV columns casually. If provenance is unclear, start a new `design_path`.
4. Relaunch one process. Existing generated names are skipped when source
   checks find them, while new random trajectories are added. The source
   counters restart, so acceptance monitoring can have different behavior on
   a continuation.

If a scheduler job dies for wall time, request a larger allocation or resume
rather than changing all quality thresholds. If disk fills, preserve CSVs and
accepted PDBs, then use cleanup settings or archive large plots/animations
before continuing. See [../SKILL.md](../SKILL.md) for routing and
[../../results-analysis/SKILL.md](../../results-analysis/SKILL.md) for artifact
interpretation.
