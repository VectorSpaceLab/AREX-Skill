# Training Configuration Reference

This reference covers DeePMD-kit training input structure from the data/configuration perspective. It deliberately stops before model selection and launch execution; route those tasks to `../training-models/SKILL.md`.

## Authoritative Schema and Docs

When the installed `dp` command is available, generate current input documentation from the package itself:

```bash
dp doc-train-input --out-type json_schema > deepmd-train.schema.json
dp doc-train-input --out-type json > deepmd-train-template.json
dp doc-train-input --out-type rst > deepmd-train-input.rst
```

Use the generated schema to validate editor autocomplete or repair invalid field names. DeePMD-kit accepts JSON input in common examples; YAML may be accepted in some workflows through the same argument parser, but JSON is the safest interchange format when uncertain.

## Single-Task Top-Level Structure

A standard single-task training input has these top-level sections:

```json
{
  "model": {
    "type_map": ["O", "H"],
    "descriptor": {"type": "se_e2_a", "sel": "auto"},
    "fitting_net": {}
  },
  "learning_rate": {"type": "exp"},
  "loss": {"type": "ener"},
  "training": {
    "training_data": {"systems": ["data_0", "data_1"], "batch_size": "auto"},
    "validation_data": {"systems": ["data_valid"], "batch_size": 1, "numb_btch": 3},
    "numb_steps": 100000,
    "seed": 1,
    "disp_freq": 100,
    "save_freq": 1000
  }
}
```

Data/config ownership:

- `model.type_map` defines model-level type order and must align with the data systems.
- `training.training_data.systems` identifies training systems.
- `training.validation_data` is optional; if present, it uses the same structure plus `numb_btch`/`numb_batch`.
- `loss` chooses which labels are needed. Do not add nonzero label weights for files absent from the systems.
- `learning_rate` and training cadence values are required for actual training but do not change data layout.

## Multi-Task Structure

Multi-task configs use task-keyed dictionaries:

```json
{
  "model": {
    "shared_dict": {
      "type_map_all": ["C", "H", "N", "O"],
      "dpa1_descriptor": {"type": "dpa1", "sel": 120}
    },
    "model_dict": {
      "task_a": {"type_map": "type_map_all", "descriptor": "dpa1_descriptor", "fitting_net": {}},
      "task_b": {"type_map": "type_map_all", "descriptor": "dpa1_descriptor", "fitting_net": {}}
    }
  },
  "loss_dict": {
    "task_a": {"type": "ener", "start_pref_f": 1000, "limit_pref_f": 1},
    "task_b": {"type": "ener", "start_pref_h": 10, "limit_pref_h": 1}
  },
  "training": {
    "model_prob": {"task_a": 1.0, "task_b": 1.0},
    "data_dict": {
      "task_a": {"training_data": {"systems": ["data/task_a"], "batch_size": 1}},
      "task_b": {"training_data": {"systems": ["data/task_b"], "batch_size": 1}}
    },
    "numb_steps": 1000
  }
}
```

Rules:

- Task keys in `model.model_dict`, `loss_dict`, `training.data_dict`, `model_prob`, and `num_epoch_dict` should match.
- Each `training.data_dict.<task>` may contain `training_data`, optional `validation_data`, and optional `stat_file`.
- Multi-task mode may require `type_map.raw` in systems even where single-task mode can treat it as optional.
- Keep label requirements task-specific: a Hessian task may require `hessian.npy`, while a sibling energy task may not.

## Data Section Fields

`training_data` and `validation_data` share most fields.

| Field | Accepted shape/value | Notes |
| --- | --- | --- |
| `systems` | string or list of strings | A system directory, parent directory searched recursively for systems, HDF5 path, or LMDB path depending on backend/data type. |
| `rglob_patterns` | list of strings | PyTorch-supported custom recursive collection patterns. Use to avoid accidental folders. |
| `batch_size` | int, list of ints, or string | See batch-size styles below. |
| `auto_prob` | string | Sampling probability rule. Alias: `auto_prob_style`. |
| `sys_probs` | list of floats | Explicit per-system probabilities. Alias: `sys_weights`. Length should match collected systems. |
| `min_pair_dist` | float | PyTorch-supported near-collision filter; can slow data loading because it checks pair distances. |
| `numb_btch` | int | Validation only. Alias: `numb_batch`. Number of validation batches per validation period. |

System discovery advice:

- Use explicit system lists while debugging. Recursive parent paths are convenient but can pick up raw, half-converted, or artifact folders.
- Keep training and validation systems separate; validation may be omitted but should not silently point to the same path unless that is intentional.
- For HDF5 use `file.hdf5#/group`; for LMDB use the LMDB path as the system value.

## Batch-Size Styles

| Value | Meaning | Use when |
| --- | --- | --- |
| integer | Same batch size for all systems | Debugging and small homogeneous systems. |
| list of integers | Per-system batch sizes | Systems differ greatly in atom count. |
| `"auto"` | Choose batch size so `batch_size * natoms >= 32` | Quick default for small systems. |
| `"auto:N"` | Choose batch size so `batch_size * natoms >= N` | Need a larger minimum atoms-per-batch. |
| `"mixed:N"` | Sample from all systems and merge into a mixed batch | TensorFlow `se_atten` mixed-system workflow only. |
| `"max:N"` | Choose batch size so `batch_size * natoms <= N`, clamped to 1 for oversized systems/frames | Memory control, especially variable-size LMDB frames. |
| `"filter:N"` | Like `max:N`, but drops systems/frames with atom count over `N` | Filtering oversized LMDB frames or NumPy systems. |

When MPI/distributed training is used, treat the configured batch size as per task/rank unless the training route specifies otherwise.

## Sampling Probabilities

`auto_prob` controls how systems are sampled:

- `prob_uniform`: every collected system has equal probability.
- `prob_sys_size`: probability is proportional to the number of batches in each system; this is the default.
- `prob_sys_size;stt_idx:end_idx:weight;...`: split the system list into index blocks and assign each block a total weight, distributing within the block by system size.

Use `sys_probs` for explicit probabilities when you need reproducible, hand-controlled weighting. Make sure its length matches the final collected system list after recursive discovery.

## Type Map Alignment

Before training, compare three things:

1. `model.type_map` or a shared type-map object in `model.shared_dict`.
2. Each system's `type_map.raw`, if present.
3. The maximum integer in each `type.raw` or `real_atom_types.npy`.

Repair rules:

- If all systems use the same direct integer convention, `type_map.raw` can be absent in standard single-task mode, but explicit maps are safer.
- If a system has local type order different from `model.type_map`, keep `type_map.raw` and let the loader remap.
- If an element appears in `type_map.raw` but not `model.type_map`, add it to the model map or remove/fix the data system.
- If `type_map.raw` has fewer entries than `max(type.raw) + 1`, the data is invalid.
- In mixed-type data, `type_map.raw` is required and `real_atom_types.npy` values must be in `[-1, 0, ..., Ntypes - 1]`.

## Loss and Label Alignment

Use the loss section to decide which labels must exist.

| Loss/model route | Required or common labels | Config signals |
| --- | --- | --- |
| Energy/force/virial | `energy.npy`, `force.npy`, optional `virial.npy` | `loss.type: "ener"` or omitted default; `start_pref_*`/`limit_pref_*`. |
| Hessian energy model | `hessian.npy` plus energy/force as configured | Nonzero `start_pref_h` or `limit_pref_h`; Hessian-capable model. |
| Atomic energy | `atom_ener.npy` | Atomic output/testing or nonzero atomic-energy prefactors. |
| Weighted force | `atom_pref.npy` | Nonzero `start_pref_pf`/`limit_pref_pf`; `use_default_pf` can avoid file need only in supported backends. |
| Generalized force | `drdq.npy` | Nonzero generalized-force prefactors and `numb_generalized_coord`. |
| Tensor dipole/polar | `dipole.npy`, `atomic_dipole.npy`, `polarizability.npy`, or `atomic_polarizability.npy` | `loss.type: "tensor"`, fitting type, `pref`, `pref_atomic`, selected atoms. |
| DOS | `dos.npy`, optional `atom_dos.npy` | `loss.type: "dos"`; fitting `numb_dos`; `start_pref_ados` for atomic DOS. |
| Property | custom property file such as `band_prop.npy` | `loss.type: "property"`; fitting `property_name` and `task_dim`. |
| Spin | `spin.npy`, `force_mag.npy` when magnetic force is supervised | `model.spin`, `loss.type: "ener_spin"`, `start_pref_fm`/`limit_pref_fm`. |

Set unused prefactors to zero if labels are missing. Do not fabricate placeholder labels unless the workflow explicitly supports defaults and the physical meaning is correct.

## `fparam` and `aparam`

- `fparam.npy` stores frame-level auxiliary parameters and is loaded when the model reports a positive frame-parameter dimension.
- `aparam.npy` stores atom-level auxiliary parameters and is loaded when the model reports a positive atomic-parameter dimension.
- If a trained/frozen model has default parameters, `fparam` may be optional for testing; otherwise it is required.
- Shape expectations follow global vs atomic rules: `fparam` is `(Nframes, dim)` and `aparam` is `(Nframes, Natoms * dim)`.

## Neighbor-Stat and Selection Pitfalls

Descriptor fields such as `sel`, `nsel`, `three_body_sel`, `e_sel`, or `a_sel` may accept `"auto"`/`"auto:factor"`, which sizes neighbor selections from data by scanning neighbor statistics.

Implications:

- Auto selection can be expensive on large recursive datasets.
- `--skip-neighbor-stat` is useful only when explicit selection values are already safe for the descriptor.
- Some dynamic-selection modes still require upper bounds to manage memory and exported static shapes.
- Large `sel` values can exceed GPU or backend limits even if CPU preflight passes.

For model-selection details, route to `../training-models/SKILL.md`; from this sub-skill, simply flag when data size and `auto` selections make the pre-training scan likely to be expensive.

## Config Repair Checklist

- Validate JSON syntax first; remove trailing commas and comments if the parser rejects them.
- Generate `dp doc-train-input --out-type json_schema` from the same installed DeePMD-kit version used for training.
- Check top-level section names: `model`, `learning_rate`, `loss`/`loss_dict`, and `training`.
- Confirm single-task uses `training.training_data`, while multi-task uses `training.data_dict` plus `model.model_dict` and `loss_dict`.
- Confirm every path in `systems` points to a trainable NumPy/HDF5/LMDB system, not raw conversion input.
- Compare `model.type_map` with every system's `type_map.raw` and integer type range.
- Align loss prefactors with labels actually present in every selected system.
- Prefer explicit system lists and small batch sizes while debugging; widen discovery and automation after preflight passes.
