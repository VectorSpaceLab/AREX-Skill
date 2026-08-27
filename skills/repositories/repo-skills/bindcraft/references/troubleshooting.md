# BindCraft cross-cutting troubleshooting

Use the narrowest route-specific troubleshooting page first. Keep the observed
error, exact settings files, GPU/backend versions, and output directory in a
campaign note before changing configuration.

## Install/import failures

- **`No GPU device found, terminating.`**: the startup JAX probe did not expose
  CUDA. Check driver visibility, `jax.devices()`, the JAX/JAXLIB CUDA variant,
  and scheduler GPU allocation. A CPU-only import does not repair this required
  gate.
- **`No module named colabdesign` or `pyrosetta`**: install into the same Python
  used to launch BindCraft and rerun `pip check` plus isolated imports. Do not
  mix a base environment with a scheduler-selected environment.
- **PyRosetta license/download errors**: use an authorized distribution and
  verify its Python ABI. Stop rather than bypassing licensing or substituting a
  superficially compatible package.
- **DSSP/DAlphaBall errors**: check that paths are set, files are executable,
  and the binary matches the host architecture. The generated skill does not
  bundle opaque binaries or repair their permissions automatically.
- **AF2 parameter not found**: verify `af_params_dir` points to the unpacked
  parameter tree, not the archive or a notebook cache. Ensure the required
  model files are readable and storage is not full.

## Configuration and launch failures

- **Missing `--settings` or file-not-found**: run the target validator, then the
  command builder with `--check-paths`. Use absolute or launch-host-relative
  paths deliberately; do not rely on the current directory inside SLURM.
- **Malformed JSON / missing key**: validate each file as the correct family.
  Do not merge target, filters, and advanced settings into one object.
- **SLURM job starts in the wrong environment**: parameterize the wrapper and
  use the scheduler's explicit environment/module setup. Do not copy another
  cluster's activation path or submit a job merely to test parsing.
- **Permission or concurrent-writer errors**: use one writable `design_path` per
  campaign, avoid concurrent processes against the same CSVs, and test parent
  directory access before launching.

## Pipeline failures

- **Low confidence, severe clashes, or too few interface contacts**: BindCraft
  moves the trajectory to a diagnostic folder and skips MPNN optimization.
  Inspect the corresponding failure counter before changing settings. Consider
  target trimming/site selection, binder length, algorithm/recycle choices, or
  loss weights one family at a time.
- **AF2 filter rejection**: early pLDDT/pTM/i_pTM/pAE checks can skip relaxation
  and interface scoring. Confirm whether thresholds are intentionally strict
  and inspect per-model values before weakening filters.
- **Low acceptance-rate stop**: the monitor can stop after `start_monitoring`
  when accepted/trajectory falls below `acceptance_rate`. Preserve the failure
  CSV and settings; increase sampling or adjust target/weights only after
  diagnosing the dominant failure mode.
- **Out-of-memory or excessive runtime**: trim the target, reduce binder length
  or recycles/model count, lower MPNN batch/sequence counts, or choose the
  documented lower-memory algorithm. Change one variable at a time and keep a
  new output directory for controlled comparisons.
- **Interrupted run**: inspect CSV/PDB consistency and free space. BindCraft has
  no dedicated `--resume` flag; relaunching the same `design_path` may reuse
  some existing names but can also add new random trajectories. Preserve the
  exact settings/filter/advanced files and do not assume a complete CSV means
  the campaign finished.

## Result interpretation

A filter pass or high `Average_i_pTM` is a structural ranking signal, not proof
of affinity, specificity, expression, or experimental success. Use the results
route to reconcile per-model agreement, clashes, RMSDs, interface metrics, and
missing prerequisites before selecting candidates. Never delete raw PDB/CSV
artifacts until a copy or archive has been verified.
