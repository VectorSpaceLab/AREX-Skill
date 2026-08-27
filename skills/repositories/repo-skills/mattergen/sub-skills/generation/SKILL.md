---
name: generation
description: "Route safe MatterGen crystal generation from pretrained or local
  checkpoints, including unconditional, property-conditional, multi-property,
  CSP composition-targeted sampling, sampling overrides, trajectories, and the
  CrystalGenerator API."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MatterGen generation

Use this sub-skill when the task is to generate inorganic crystal candidates with
MatterGen 1.0.3. It owns checkpoint selection, conditioning, CSP compositions,
sampling configuration, output artifacts, and the public `CrystalGenerator` API.
It does **not** own training, fine-tuning, relaxation/evaluation, dataset
creation, or paper-result interpretation; route those tasks to the appropriate
MatterGen skill instead.

## Route before running

1. Decide whether the checkpoint is a named pretrained model or a local
   checkpoint directory. `pretrained_name` and `model_path` are mutually
   exclusive, and at least one is required.
2. Decide whether the request is unconditional, property-conditioned, or CSP.
   CSP means fixed element counts and requires a CSP-trained checkpoint plus the
   `csp` sampling config; a normal base checkpoint cannot be turned into CSP by
   adding a composition argument.
3. Check that every requested property is a condition the selected checkpoint
   was trained to accept. For the catalog and known condition sets, read
   [model-overview.md](references/model-overview.md).
4. Bound `batch_size * num_batches`, GPU memory, trajectory storage, and output
   location before loading a model. Use the safe validator first:
   [scripts/generate_materials.py](scripts/generate_materials.py).
5. Read [workflows.md](references/workflows.md) for the matching invocation and
   [troubleshooting.md](references/troubleshooting.md) before retrying failures.

## Supported routes

- **Unconditional:** use `mattergen_base` or `mp_20_base` with no property map
  and no target composition. `diffusion_guidance_factor=0.0` is unconditional
  behavior.
- **Single property:** use a compatible fine-tuned model and pass a mapping such
  as `{'dft_mag_density': 0.15}`. The CLI is Fire-based; quote the whole map
  and do not put whitespace around its key/value separator.
- **Multiple properties:** pass one mapping, for example
  `{'energy_above_hull': 0.05, 'chemical_system': 'Li-O'}`, to a checkpoint
  trained jointly for those conditions. A property name being globally known
  does not prove that every checkpoint supports it.
- **CSP:** pass a list of element-count mappings, such as
  `[{'Na': 1, 'Cl': 1}]`, and `--sampling-config-name=csp`. The CSP config omits
  atomic-number predictor/corrector parts because atom types are fixed by the
  requested composition. Use a CSP-trained local model; the public pretrained
  catalog is primarily the non-CSP catalog.
- **Python API:** construct `MatterGenCheckpointInfo`, then `CrystalGenerator`,
  and call `generate`. Use the exact public signatures in
  [api-reference.md](references/api-reference.md); do not reproduce private
  model-loading internals in a caller script.

## Safe execution procedure

1. Run the bundled helper with `--help`, then without `--run`, to parse and
   validate the request. It never downloads a checkpoint or starts sampling by
   default. Fix errors before using `--run`.
2. For a Hub model, verify network/cache permission and choose a small smoke
   batch first. `MatterGenCheckpointInfo.from_hf_hub(...)` downloads missing
   files only when explicitly running. For a local model, verify its directory
   contains `config.yaml` and hydrated checkpoint files; a Git-LFS pointer is
   not a usable checkpoint.
3. Set `--record-trajectories=False` (native CLI spelling) when trajectory ZIPs
   are not needed. Keep the first run small; increase batch size only after a
   successful memory smoke test. MatterGen selects CUDA when available, then
   MPS, then CPU; generation is substantially slower and may be impractical on
   CPU.
4. Run into a new or deliberately chosen output directory. Never assume a
   partially written output is a complete sample set.
5. Inspect the returned/generated structure count and the expected files:
   `generated_crystals_cif.zip`, `generated_crystals.extxyz`, and, when enabled,
   `generated_trajectories.zip`. Preserve the resolved checkpoint/config and
   sampling overrides with the experiment record outside this skill tree.

## Conditioning and guidance rules

`properties_to_condition_on` is a `dict` whose keys must be model-supported
property source IDs. `diffusion_guidance_factor` is the classifier-free guidance
weight: 0 selects the unconditional score, 1 selects the conditional score,
and larger nonnegative values increasingly favor the requested condition while
usually reducing diversity/realism. Guidance cannot add a missing property
head, repair malformed values, or make an incompatible checkpoint conditional.

`sampling_config_overrides` are Hydra override strings. The installed default
sampling configuration uses 1,000 diffusion steps and atom-number denoising;
the installed CSP configuration uses composition conditioning and omits
atomic-number denoising. Use overrides only for known config keys and record
them exactly. Avoid changing sampler fields until a baseline completes.

## Failure recovery

- Missing assets: stop and acquire/hydrate the selected checkpoint (Hub or LFS);
  do not confuse CUDA readiness with asset readiness.
- Import/backend errors: run the helper's validation without `--run`, then use
  the environment's public `python -c` import/help probes. Check optional ASE,
  PyTorch Geometric CUDA wheels, `pymatgen`, Hydra, and MatterSim dependencies;
  do not silently switch to a different package version.
- Config/condition errors: reduce to an unconditional one-batch run, then add
  one condition, then multiple conditions. For CSP, switch both the checkpoint
  and config rather than only changing the CLI flag.
- Out-of-memory or stalled jobs: lower `batch_size`, lower `num_batches`, turn
  off trajectories, and retry in a fresh output directory. Do not infer model
  quality from an interrupted run.
- Output errors: ensure the output directory is writable and has space; verify
  ZIP members and frame count before downstream evaluation.

## Bundled operating material

- [API signatures and contracts](references/api-reference.md)
- [CLI, API, CSP, and override workflows](references/workflows.md)
- [Checkpoint catalog and model limits](references/model-overview.md)
- [Failure diagnosis and recovery matrix](references/troubleshooting.md)
- [Safe parser/validator and explicit-run helper](scripts/generate_materials.py)
