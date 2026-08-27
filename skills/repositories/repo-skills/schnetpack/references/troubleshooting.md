# Cross-Cutting Troubleshooting

Use this root troubleshooting guide for broad SchNetPack failures. Route workflow-specific fixes to the sub-skill references after identifying the surface.

## Install or Import Fails

Symptoms:

- `ModuleNotFoundError: schnetpack`.
- `pip check` reports PyTorch, Lightning, Hydra, ASE, matscipy, or NumPy conflicts.
- Import succeeds in one shell but CLI commands are unavailable in another.

Fix:

1. Verify the environment uses Python `>=3.12` for SchNetPack `2.2.0`.
2. Run `python -m pip show schnetpack` and `python -m pip check` in the same environment used by the agent or CLI.
3. Run `python scripts/schnetpack_import_check.py --json` from this skill to check imports and signatures.
4. If command scripts are missing, reinstall SchNetPack in the target environment or call module APIs directly where possible.
5. Prefer CPU PyTorch for inspection and docs tasks unless the user explicitly needs CUDA execution.

## PyTorch or Backend Confusion

Symptoms:

- CUDA is unavailable even though PyTorch imports.
- MD or training tries to use GPU on a CPU-only host.
- A deployment/build request asks for CUDA, LAMMPS, or compiler changes.

Fix:

- Use CPU examples (`device=cpu`, `device="cpu"`) unless the environment proves CUDA support.
- Check `python -c "import torch; print(torch.__version__, torch.cuda.is_available())"`.
- Do not install CUDA, patch LAMMPS, or modify compiler/toolchain state without explicit user approval.
- For `spkmd`, add `device=cpu` on CPU-only hosts.

## Hydra Override Errors

Symptoms:

- `Missing mandatory value`, unknown config group, or override parse errors.
- User uses `model.representation=painn` when they meant `model/representation=painn`.
- User forgets `+` when adding thermostat/barostat groups to a null MD config.

Fix:

- Route training/prediction errors to `sub-skills/training-configs/references/troubleshooting.md`.
- Route MD config errors to `sub-skills/interfaces-md/references/troubleshooting.md`.
- Remember: slash selects a config group; dot edits a field; `+` adds missing/null entries.
- Use `--help` or `--cfg job` style config inspection before launching long compute.

## Dataset or Unit Errors

Symptoms:

- `Dataset does not have a distance unit set`.
- `Dataset does not have a property units set`.
- Requested property is absent from the ASE DB.
- Stale split files or split sizes do not match the current dataset.

Fix:

- Route to `sub-skills/data-pipelines/SKILL.md`.
- Use `scripts/convert_ase_units.py` under `data-pipelines` on a copy of a legacy ASE DB.
- Confirm `_distance_unit`, `_property_unit_dict`, property names, atomrefs, and split arrays before training.
- Do not use `A` for Angstrom; use `Ang` or `Angstrom` depending on ASE unit conventions.

## Model Output and Property Key Errors

Symptoms:

- Force/stress outputs are missing.
- `ModelOutput` target keys do not match batch keys.
- Postprocessors produce unexpected offsets or dtypes.
- `Atomwise` returns no global output.

Fix:

- Route to `sub-skills/models-atomistic/SKILL.md`.
- Align `Atomwise.output_key`, `Forces.energy_key`, `Forces.force_key`, `ModelOutput.name`, and dataset property names.
- If `Atomwise(aggregation_mode=None)`, set `per_atom_output_key`.
- For forces/stress, verify required derivatives and response modules before moving to ASE/MD.

## ASE, MD, or LAMMPS Runtime Errors

Symptoms:

- ASE calculator returns missing energy/forces/stress.
- `spkmd` requires `simulation_dir`, `system.molecule_file`, `calculator.model_file`, or cutoff.
- LAMMPS deployment or TorchScript conversion fails.

Fix:

- Route to `sub-skills/interfaces-md/SKILL.md`.
- Match model output keys and units to calculator settings.
- Keep MD smoke tests bounded and CPU-first.
- Use the bundled LAMMPS deployment helper only after checking model compatibility.
- Treat LAMMPS source patch/build steps as unsafe-by-default environment mutation.

## Safe Escalation Path

1. Run the root import and CLI checker scripts.
2. Identify the failing workflow: data, training/config, model components, or interfaces/MD.
3. Read the nearest sub-skill troubleshooting reference.
4. Use tiny local fixtures or help/config checks before running long training, downloads, MD, GPU jobs, or external builds.
