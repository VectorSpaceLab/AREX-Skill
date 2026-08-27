---
name: data-config
description: "Inspect DeePMD-kit data systems and draft or repair training input
  configuration before training or testing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: LGPL 3.0
---

# DeePMD-kit Data and Training Configuration

Use this sub-skill when the task is to prepare, inspect, validate, or repair DeePMD-kit system data directories and training input JSON/YAML before launching training.

## Route Here When

- The user has a DeePMD system directory and asks whether it is valid.
- The task mentions `type.raw`, `type_map.raw`, `nopbc`, `set.*`, `coord.npy`, `box.npy`, labels, or mixed-type data.
- The task is to draft or repair `training_data`, `validation_data`, `type_map`, `model`, `loss`, `learning_rate`, or `training` sections.
- The user needs data/layout guidance for energy-force-virial, Hessian, tensor, DOS, property, spin, `fparam`, or `aparam` supervision.
- The task asks how to use `dp doc-train-input`, DP-GUI-style JSON schema output, HDF5 paths, LMDB systems, or dpdata conversion before training.

## Route Elsewhere

- For choosing descriptors, fitting nets, loss schedules, launching `dp train`, freezing checkpoints, or reading training logs, use `../training-models/SKILL.md`.
- For testing frozen models, `DeepPot` inference, `dp test`, model deviation, descriptors, compression, conversion, or bias changes, use `../inference-model-ops/SKILL.md`.
- For installing DeePMD-kit, selecting TensorFlow/PyTorch/JAX/Paddle backends, or resolving package import problems, use `../installation-backends/SKILL.md`.

## Core Concepts

- A DeePMD **system** is one data folder or one supported data store entry; a **frame** is one configuration within a system.
- Standard NumPy systems group frames with the same atom count and atom-type ordering under one folder.
- `type.raw` is required and defines integer atom type indexes for the system; `type_map.raw` is optional for standard data but strongly recommended when `model.type_map` is set.
- `nopbc` marks a non-periodic system. Periodic systems need `box.npy` in each `set.*`; non-periodic systems should omit or ignore boxes consistently.
- Input frame properties include `coord`, `box`, `fparam`, `aparam`, and `numb_copy`/`prob`-style frame weighting.
- Label files are loaded only when the chosen model/loss/test path requests them; missing labels are harmless only when their loss prefactors or model features do not require them.
- Mixed-type systems use placeholder `type.raw`, required `type_map.raw`, and per-frame `real_atom_types.npy`; type `-1` is a virtual atom used for padding.

## First Inspection Pass

1. Identify the system path type: NumPy directory, HDF5 path using `file.hdf5#/group`, LMDB file, or raw text waiting for conversion.
2. For NumPy directories, run the bundled inspector:

   ```bash
   python sub-skills/data-config/scripts/inspect_deepmd_system.py /path/to/system --pretty
   ```

3. Read `references/data-formats.md` to interpret the summary and warnings.
4. Confirm that `model.type_map` matches the intended element order and is compatible with every system's `type.raw` or `type_map.raw`.
5. Confirm labels match the requested training target: do not add loss prefactors for missing labels.
6. For JSON/YAML input files, generate authoritative schema/reference output from the installed CLI when available:

   ```bash
   dp doc-train-input --out-type json_schema > deepmd-train.schema.json
   dp doc-train-input --out-type rst > deepmd-train-input.rst
   ```

## Data Layout Workflow

- Use `references/data-formats.md` for the file tree, shape expectations, label ownership, HDF5/LMDB/raw conversion notes, and mixed-type rules.
- Use `scripts/inspect_deepmd_system.py` for safe local checks that do not import `deepmd` or mutate data.
- Treat the inspector as a preflight, not as a full DeePMD loader replacement: it flags likely shape and consistency errors, but the final backend loader may enforce additional descriptor/loss-specific constraints.
- For raw text data, convert to NumPy format before training. Raw `coord.raw`, `box.raw`, `energy.raw`, `force.raw`, and similar files are evidence/inputs for conversion, not a directly trainable format.
- For dpdata workflows, use dpdata to convert external molecular formats into DeePMD NumPy/HDF5 systems, then inspect the converted result here.

## Training Input Workflow

- Use `references/training-config-reference.md` for the top-level structure, single-task and multi-task data sections, batch-size styles, and label-to-loss mapping.
- Start from a minimal config with top-level `model`, `learning_rate`, `loss`, and `training` for single-task workflows.
- Put systems under `training.training_data.systems`; use `training.validation_data.systems` only when validation data exists.
- For multi-task workflows, put per-task `training_data`, `validation_data`, and optional `stat_file` under `training.data_dict.<task>` and pair them with matching `model.model_dict` and `loss_dict` keys.
- Prefer explicit `batch_size` during debugging. Use `auto`, `auto:N`, `max:N`, or `filter:N` after confirming atom counts and memory expectations.
- Avoid expensive neighbor-stat surprises: descriptor selections such as `sel: "auto"` trigger neighbor statistics unless the training route explicitly skips or constrains it.

## Label Ownership Quick Map

- Energy models: `energy.npy`, `force.npy`, optional `virial.npy`, `hessian.npy`, `atom_ener.npy`, `atom_pref.npy`, `fparam.npy`, `aparam.npy`.
- Hessian workflows: add `hessian.npy` and nonzero `start_pref_h`/`limit_pref_h` only for branches that own Hessian labels.
- Tensor workflows: use `dipole.npy`/`atomic_dipole.npy` or `polarizability.npy`/`atomic_polarizability.npy` according to global vs atomic tensor loss.
- DOS workflows: use `dos.npy` and optionally `atom_dos.npy`; the output dimension must match the fitting-net DOS grid.
- Property workflows: use the file named by the property fitting configuration, for example `band_prop.npy`.
- Spin workflows: include `spin.npy` when the model has spin inputs and `force_mag.npy` when magnetic force metrics/loss are required.
- Mixed-type workflows: include `real_atom_types.npy` in every `set.*`; virtual atoms use `-1` and their atomic labels should be zero padded.

## Repair Heuristics

- If atom labels load but forces are permuted or the model reports unexpected element errors, inspect `type_map.raw` versus `model.type_map` before changing model architecture.
- If periodic training fails on boxes, either add valid `box.npy` for every frame or add `nopbc` and remove PBC assumptions from downstream tasks.
- If validation finds missing virials, set virial loss prefactors to zero or provide `virial.npy`; do not leave nonzero virial weights with absent labels.
- If a folder contains multiple formulas, split by formula for standard data or convert to mixed-type with consistent `Natoms`/virtual atom padding.
- If JSON/YAML fails validation, regenerate schema with `dp doc-train-input` from the installed package and compare field names, aliases, and backend-specific options.
- If data loading is slow or neighbor statistics are expensive, reduce system discovery breadth, use explicit `systems` lists, set explicit neighbor selections, or debug with smaller converted systems.

## References

- `references/data-formats.md`: self-contained data-system format, shape, label, mixed-type, HDF5, LMDB, and conversion guidance.
- `references/training-config-reference.md`: training input structure, data sections, batch options, schema generation, and label/loss alignment.
- `references/troubleshooting.md`: symptom-driven fixes for type maps, boxes, mixed-type, labels, invalid configs, sparse formulas, and neighbor statistics.
- `scripts/inspect_deepmd_system.py`: standalone NumPy-directory preflight inspector that prints JSON summary and warnings.
