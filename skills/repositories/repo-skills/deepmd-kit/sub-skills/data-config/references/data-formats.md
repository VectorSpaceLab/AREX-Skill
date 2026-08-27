# DeePMD-kit Data Formats

This reference distills the DeePMD-kit system layout a future agent needs before training, validation, or frozen-model testing. It is self-contained and does not require reopening the original repository docs.

## System, Frame, and Formula

- A **system** is a data container with one atom-type definition and one or more frame sets.
- A **frame** is one atomic configuration: coordinates, optional box, optional frame parameters, and optional labels.
- Standard systems assume all frames in the folder share the same atom count and atom ordering/type pattern.
- If data contains multiple formulas in one source collection, prefer splitting into separate standard systems. Use mixed-type only when the descriptor/backend workflow supports it and all frames can be represented with a consistent atom count or virtual padding.
- A **sparse formula** problem occurs when rare formulas produce very small systems. Mixed-type data can reduce sparsity for compatible descriptors, but it changes the required files and type handling.

## Standard NumPy System Tree

A typical trainable NumPy system looks like:

```text
system/
  type.raw
  type_map.raw           # optional but recommended
  nopbc                  # optional marker for non-periodic systems
  set.000/
    coord.npy
    box.npy              # required for periodic systems
    energy.npy           # optional label
    force.npy            # optional label
    virial.npy           # optional label
  set.001/
    coord.npy
    box.npy
    energy.npy
    force.npy
```

Rules:

- `type.raw` is required at the system root and contains `Natoms` integer type indexes, usually whitespace-separated.
- `type_map.raw` contains type names ordered by integer type id. If present, index `0` maps to the first name, index `1` to the second, and so on.
- `set.*` directories contain NumPy `.npy` arrays. DeePMD-kit also recognizes HDF5 storage with equivalent keys, but raw text files are not directly trained.
- `coord.npy` is required in every set. It is usually shaped `(Nframes, Natoms * 3)` or equivalent data that reshapes to that size.
- `box.npy` is required for periodic systems and shaped `(Nframes, 9)` in `XX XY XZ YX YY YZ ZX ZY ZZ` order.
- An empty root-level `nopbc` file marks a non-periodic system. Non-periodic data should not rely on boxes.
- Every per-frame `.npy` file in one `set.*` should have the same first dimension `Nframes`.

## Core Property Files

| File | Location | Required | Shape convention | Notes |
| --- | --- | --- | --- | --- |
| `type.raw` | root | Yes | `Natoms` | Integer atom type ids starting at 0. |
| `type_map.raw` | root | Recommended | `Ntypes` names | Required for mixed-type and strongly recommended with `model.type_map`. |
| `nopbc` | root | Optional | marker | If present, system is non-periodic. |
| `coord.npy` | `set.*` | Yes | `(Nframes, Natoms * 3)` | Coordinates in Å. |
| `box.npy` | `set.*` | Periodic only | `(Nframes, 9)` | Cell matrix flattened row-major. |
| `fparam.npy` | `set.*` | Model-dependent | `(Nframes, dim)` | Extra frame parameters. |
| `aparam.npy` | `set.*` | Model-dependent | `(Nframes, Natoms * dim)` | Extra atomic parameters. |
| `numb_copy.npy` | `set.*` | Optional | `(Nframes,)` or `(Nframes, 1)` | Frame copy/weight count where supported. |

## Label Files and Ownership

Only provide or require a label when the selected fitting/loss/test path uses it. Missing optional labels are acceptable when the relevant prefactors are zero or the model does not request that target.

| Target | Common file | Shape convention | Configuration owner |
| --- | --- | --- | --- |
| Energy | `energy.npy` | `(Nframes,)` or `(Nframes, 1)` | `loss.type: ener` or default energy loss. |
| Force | `force.npy` | `(Nframes, Natoms * 3)` | Energy/force training and most `dp test` energy models. |
| Virial | `virial.npy` | `(Nframes, 9)` | Nonzero virial prefactors; periodic systems only for metrics. |
| Hessian | `hessian.npy` | `(Nframes, Natoms * 3 * Natoms * 3)` flattened | Hessian-capable model/loss with nonzero Hessian prefactors. |
| Atomic energy | `atom_ener.npy` | `(Nframes, Natoms)` | Atomic-energy output/testing. |
| Atomic force weights | `atom_pref.npy` | `(Nframes, Natoms)` | Weighted force loss; may repeat over 3 force components internally. |
| Generalized force derivative | `drdq.npy` | `(Nframes, Natoms * 3 * Ngen)` | Generalized force loss with `numb_generalized_coord`. |
| Dipole | `dipole.npy` | `(Nframes, 3)` or selected-atom tensor convention | Tensor fitting/loss. |
| Atomic dipole | `atomic_dipole.npy` or normalized `atom_dipole` key | `(Nframes, Natoms * 3)` | Atomic tensor fitting/loss. |
| Polarizability | `polarizability.npy` | `(Nframes, 9)` | Tensor fitting/loss. |
| Atomic polarizability | `atomic_polarizability.npy` or normalized `atom_polarizability` key | `(Nframes, Natoms * 9)` | Atomic tensor fitting/loss. |
| DOS | `dos.npy` | `(Nframes, numb_dos)` | DOS fitting/loss. |
| Atomic DOS | `atom_dos.npy` | `(Nframes, Natoms * numb_dos)` | Atomic/site-projected DOS. |
| Property | e.g. `band_prop.npy` | `(Nframes, task_dim)` or model-specific | Property fitting where `property_name` selects the file stem. |
| Spin vector | `spin.npy` | `(Nframes, Natoms * 3)` | Spin-enabled models. |
| Magnetic force | `force_mag.npy` | `(Nframes, Natoms * 3)` | Spin magnetic force loss/metrics. |
| Charge/spin embedding | `charge_spin.npy` | `(Nframes, 2)` or configured dimension | Charge-spin embedding when no default is available. |
| Electric field | `efield.npy` | `(Nframes, Natoms * 3)` | Models with e-field input. |

Shape notes:

- DeePMD-kit loaders frequently flatten atomic arrays in files and reshape internally. The important invariant is that `array.size == Nframes * Natoms * ndof` for atomic arrays.
- Global arrays require `array.size == Nframes * ndof`.
- `hessian.npy` may appear as a very wide flattened matrix; verify total size rather than expecting a single canonical rank.
- The loader normalizes keys beginning with `atomic_` to an `atom_` convention internally for some tensor paths, but file naming should still follow the target workflow's documented convention.

## Type Maps and Remapping

`type_map.raw` and `model.type_map` are the most common source of silent data/model mismatch.

- If `model.type_map` is omitted, `type.raw` values in all systems should already use the same integer meaning.
- If `model.type_map` is set and each system has `type_map.raw`, DeePMD-kit can map system-local type ids into the model type order.
- Every name in a system `type_map.raw` must appear in `model.type_map` when remapping is needed.
- `type_map.raw` may include unused element names; that can be valid, but confirm `len(type_map.raw) > max(type.raw)`.
- Do not reorder `model.type_map` casually after data statistics or checkpoints exist. Element order affects atom type ids, energy bias, and downstream model compatibility.

Quick check:

```text
type.raw:      0 1 0 1
type_map.raw:  O H
model.type_map: ["H", "O"]
```

This is valid only if the loader remaps with `type_map.raw`; the model type ids after remapping become `1 0 1 0`. Without `type_map.raw`, the same `type.raw` would be interpreted directly in model order.

## Mixed-Type Format

Mixed-type systems are designed for sparse formula collections where frames share total atom count, or can be padded with virtual atoms, but have different per-frame atom types.

Mixed-type tree:

```text
system/
  type.raw                 # placeholder, often all zeros, length Natoms
  type_map.raw             # required, all possible real element names
  set.000/
    coord.npy
    box.npy
    energy.npy
    force.npy
    real_atom_types.npy
```

Rules:

- `real_atom_types.npy` is required in every `set.*` and shaped `(Nframes, Natoms)`.
- Values in `real_atom_types.npy` index into `type_map.raw`; `-1` means a virtual padding atom.
- Virtual atoms should have zero-valued atomic labels such as force entries because they do not contribute to fitting properties.
- All `set.*` directories inside a system must consistently be mixed-type or standard; do not mix `real_atom_types.npy` in only some sets.
- All systems combined in a training dataset should consistently use mixed-type or standard format.
- Mixed-type support is descriptor/backend-dependent. Route descriptor choice and training launch details to `../training-models/SKILL.md` after data validity is established.

## Multiple Formulas in One Folder

For standard data, avoid placing frames with different formulas in one system because `type.raw` is system-level, not frame-level.

Preferred decisions:

1. Split source frames into one standard system per formula and use a list under `training.training_data.systems`.
2. If many formulas are sparse and a supported descriptor is intended, convert to mixed-type with `real_atom_types.npy` and virtual padding.
3. If formulas also differ in atom count and mixed-type is not appropriate, keep separate systems and manage probabilities with `auto_prob` or `sys_probs`.

## HDF5 Systems

HDF5 stores the same logical tree inside groups. DeePMD-kit paths use `#` to separate the file path from the group path:

```text
/path/to/data.hdf5#/H2O
```

Requirements:

- The group path must start with `/`.
- Keys mirror NumPy-system paths, for example `/H2O/type.raw`, `/H2O/set.000/coord.npy`, and `/H2O/set.000/force.npy`.
- HDF5 is useful for large collections on clusters where many small filesystem files are expensive.
- The bundled inspector currently targets filesystem NumPy directories; use DeePMD/dpdata tooling for HDF5 validation.

## LMDB Systems

LMDB data can be referenced directly in `training_data.systems`, commonly as a single `.lmdb` path. Useful config interactions:

- `systems` may be a string for one LMDB store.
- `batch_size: "max:N"` caps approximate atom count per batch; for LMDB it uses per-frame local atom counts.
- `batch_size: "filter:N"` behaves like `max:N` and additionally drops frames whose atom count exceeds `N`.
- Frozen-model testing may split LMDB frames by local atom count internally, so variable-size frame handling differs from standard NumPy systems.

## Raw Text and Conversion

Raw text files such as `coord.raw`, `box.raw`, `force.raw`, `energy.raw`, and `virial.raw` are not directly trainable. They are conversion inputs.

- Each raw frame is one text line.
- Global labels have `ndof` columns per frame; atomic labels have `Natoms * ndof` columns per frame.
- Convert raw text into `set.*/*.npy` before training.
- After conversion, inspect the generated NumPy system rather than the original raw folder.
- If using dpdata, convert external formats to DeePMD NumPy/HDF5, then apply this reference and inspector to the result.

## Preflight Checklist

- `type.raw` exists and contains integers.
- `type_map.raw`, if present, has enough names for the maximum `type.raw` id.
- Each `set.*` contains `coord.npy` with a first dimension matching every other per-frame file.
- Periodic systems contain `box.npy`; non-periodic systems contain `nopbc` and do not rely on virial/box metrics.
- Label files exist only when the model/loss requires them, or missing labels have zero prefactors/default paths.
- Mixed-type systems have `real_atom_types.npy` in every set and `type_map.raw` at the root.
- Multi-system training uses compatible standard-vs-mixed mode and compatible type maps.
- Large or recursive `systems` discovery does not accidentally include invalid converted folders, source raw folders, or artifact directories.
