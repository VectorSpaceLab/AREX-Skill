# Data Formats and Pipeline Recipes

SchNetPack 2.2.0 stores atomistic datasets as ASE database files and loads them through `schnetpack.data`. The public data path is independent of the original repository checkout: agents only need an installed `schnetpack` package plus its runtime dependencies.

## ASE DB Contract

A SchNetPack-compatible ASE DB must contain three global metadata entries:

- `_distance_unit`: the unit string for positions and cells, normally `Ang`.
- `_property_unit_dict`: a dictionary mapping every training property to a unit string, for example `{"energy": "kcal/mol", "forces": "kcal/mol/Ang"}`.
- `atomrefs`: a dictionary mapping extensive properties to per-element reference arrays; use `{}` when there are no atom references.

Rows store structures as ASE `Atoms` plus binary property arrays under `row.data`. Property names must match `_property_unit_dict`; missing required properties fail when adding or loading rows.

Prefer `Ang` or `Angstrom` for Angstrom distances. Avoid `A`: in ASE unit names, `A` means Ampere and is rejected by the bundled conversion helper for distance metadata.

## Create a Tiny Custom Dataset

Use this pattern for smoke tests, examples, and small user-provided data. All systems in one dataset must have the same declared property keys.

```python
import numpy as np
from ase import Atoms
from schnetpack.data import ASEAtomsData

atoms_list = [Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74]])]
property_list = [{"energy": np.array([-1.1]), "forces": np.zeros((2, 3))}]

dataset = ASEAtomsData.create(
    "tiny.db",
    distance_unit="Ang",
    property_unit_dict={"energy": "eV", "forces": "eV/Ang"},
    atomrefs={},
)
dataset.add_systems(atoms_list=atoms_list, property_list=property_list)
print(len(dataset), dataset.available_properties, dataset.units)
```

Notes:

- `datapath` must end in `.db`; creation fails if the file already exists.
- `add_systems` can accept `atoms_metadata_list` for row-level metadata used by split strategies or diagnostics.
- If `atoms_list` is omitted, each property dict must include SchNetPack structure keys (`Z`, `R`, `cell`, `pbc` via `schnetpack.properties`).
- Undeclared properties are ignored with a warning; missing declared properties raise `AtomsDataError`.

## Load and Inspect a Dataset

```python
from schnetpack.data import ASEAtomsData

dataset = ASEAtomsData(
    "tiny.db",
    load_properties=["energy", "forces"],
    distance_unit="Ang",
    property_units={"energy": "eV", "forces": "eV/Ang"},
)

print(dataset.metadata)
print(dataset.available_properties)
print(dataset.units)
print(dataset.atomrefs)
example = dataset[0]
print(example.keys())
```

`ASEAtomsData.__getitem__` returns tensors. With structure loading enabled, batches include atomic numbers, positions, cell, periodic boundary flags, atom counts, row index, and selected properties. Set `load_structure=False` only for workflows that do not need coordinates.

Use `iter_properties(indices=..., load_properties=..., load_structure=..., load_metadata=True)` when metadata or a controlled row subset is needed without constructing data loaders.

## Build an AtomsDataModule

Use `AtomsDataModule` when a task needs train/validation/test splits, loaders, transforms, unit conversion, or PyTorch Lightning integration.

```python
import schnetpack as spk
import schnetpack.transform as trn

data = spk.data.AtomsDataModule(
    datapath="tiny.db",
    batch_size=2,
    num_train=1,
    num_val=0,
    num_test=0,
    split_file="split.npz",
    load_properties=["energy", "forces"],
    distance_unit="Ang",
    property_units={"energy": "eV", "forces": "eV/Ang"},
    transforms=[
        trn.ASENeighborList(cutoff=5.0),
        trn.CastTo32(),
    ],
    num_workers=0,
    pin_memory=False,
)
data.prepare_data()
data.setup()
print(len(data.train_dataset), len(data.val_dataset), len(data.test_dataset))
print(next(iter(data.train_dataloader())).keys())
```

Transform placement matters:

- `transforms` applies to train, validation, and test unless phase-specific transforms override it.
- `train_transforms`, `val_transforms`, and `test_transforms` replace the shared list for that split.
- Neighbor-list transforms such as `ASENeighborList`, `TorchNeighborList`, `MatScipyNeighborList`, and `VesinNeighborList` prepare pair indices before batching.
- Offset/statistics transforms such as `RemoveOffsets` typically need an initialized `AtomsDataModule` because they read training statistics or atomrefs.
- Add output-module and postprocessing choices in `../models-atomistic/SKILL.md`, not here.

## Split Files

`AtomsDataModule` uses `split_file="split.npz"` by default. If the file exists, SchNetPack loads `train_idx`, `val_idx`, and `test_idx` from it and checks requested sizes against array lengths. If it does not exist, `num_train` and `num_val` are required and a new split is saved.

Split sizes may be absolute integers or relative floats in `[0, 1]`; one split can be `None` or negative to take the remaining examples. For tiny validation data, prefer explicit integers to avoid floor rounding surprises.

Quick split inspection:

```python
import numpy as np

split = np.load("split.npz")
for key in ["train_idx", "val_idx", "test_idx"]:
    values = split[key]
    print(key, len(values), values[:10].tolist())
```

When a dataset changes length or the requested counts change, delete or rename the old split file before calling `setup()`.

## Built-in Dataset Modules

Built-in dataset modules subclass `AtomsDataModule`. They can download or convert benchmark data in `prepare_data()` if the target DB is missing; avoid calling them in expensive diagnostic loops unless the data already exists locally.

| Module | Common properties | Native units/notes | Extra arguments |
| --- | --- | --- | --- |
| `QM9` | `energy_U0`, `energy_U`, `enthalpy_H`, `free_energy`, `homo`, `lumo`, `gap`, `zpve`, plus rotational/dipole/polarizability/heat-capacity fields | Positions `Ang`; several energies start as `Ha`; configs often convert selected properties to `eV` | `remove_uncharacterized` |
| `MD17` | `energy`, `forces` | `kcal/mol`, `kcal/mol/Ang`; validates `molecule` metadata | `molecule` |
| `rMD17` | `energy`, `forces` | `kcal/mol`, `kcal/mol/Ang`; includes atomrefs and optional predefined splits | `molecule`, `split_id` |
| `MD22` | `energy`, `forces` | GDML-style data with `kcal/mol`, `kcal/mol/Ang`; larger molecules | `molecule` |
| `ANI1` | `energy` | `Hartree`; includes self-energy atomrefs | `num_heavy_atoms`, `high_energies` |
| `ISO17` | `total_energy`, `atomic_forces` | `eV`, `eV/Ang`; `datapath` is a folder and `fold` selects a DB under it | `fold` |
| `QM7X` | `energy`, `forces`, `Eat`, `EPBE0`, `EMBD`, `FPBE0`, `FMBD`, `rmsd` | mostly `eV`, `eV/Ang`, `Ang`; supports group-style splits | `raw_data_path`, filtering flags |
| `MaterialsProject` | `formation_energy_per_atom`, `energy_per_atom`, `band_gap`, `total_magnetization` | `eV` and unitless magnetization; requires compatible API credentials and optional packages | `apikey` |
| `OrganicMaterialsDatabase` | `band_gap` | `eV`; converts a user-provided raw archive | `raw_path` |
| `TMQM` | `Electronic_E`, `Dispersion_E`, `HOMO_Energy`, `LUMO_Energy`, `HL_Gap`, `Dipole_M`, `Polarizability`, `Metal_q` | `Ha`, `Debye`, `a0 a0 a0`, `e` | none beyond common data-module args |

Hydra data configs use `_target_` values such as `schnetpack.data.AtomsDataModule` for custom data and `schnetpack.datasets.QM9` for built-ins. Full experiment CLI construction belongs in `../training-configs/SKILL.md`.

## Conversion and Metadata Repair

For an old ASE DB without `_distance_unit` or `_property_unit_dict`, first make a copy, then run the bundled helper:

```bash
python sub-skills/data-pipelines/scripts/convert_ase_units.py tiny.db \
  --distunit Ang \
  --propunit energy:eV,forces:eV/Ang
```

The helper also converts legacy `atomrefs` plus `atref_labels` metadata into the SchNetPack 2 dictionary form and can expand selected property arrays:

```bash
python sub-skills/data-pipelines/scripts/convert_ase_units.py tiny.db \
  --expand-property-dims dipole polarizability
```

Use `--dry-run` to print the planned metadata changes without writing them.

## Minimal Validation Checklist

- `ASEAtomsData("file.db")` opens without unit metadata errors.
- `dataset.available_properties` contains every property requested by training or prediction.
- `dataset.units` and `dataset.atomrefs` are sane for the model target.
- `dataset[0]` returns tensors with expected shapes, especially scalar energies as shape `(1,)` and forces as `(n_atoms, 3)`.
- `AtomsDataModule(...).setup()` creates or loads the intended split and all split lengths match the request.
- A one-batch loader iteration succeeds with the same transforms intended for training.
