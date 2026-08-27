# Data API Reference

This reference focuses on APIs needed to create, inspect, convert, split, and validate SchNetPack atomistic datasets. Model architecture and training command construction are intentionally routed to sibling sub-skills.

## Imports

```python
from schnetpack.data import (
    ASEAtomsData,
    AtomsDataFormat,
    AtomsDataModule,
    AtomsLoader,
    RandomSplit,
    SubsamplePartitions,
    GroupSplit,
    create_dataset,
    load_dataset,
    calculate_stats,
    estimate_atomrefs,
)
import schnetpack.transform as trn
```

Verified package facts for SchNetPack 2.2.0: import name `schnetpack`, Python `>=3.12`, CPU PyTorch is sufficient for API and CLI inspection, and CLI help is available for `spktrain`, `spkpredict`, `spkmd`, `spkconvert`, and `spkdeploy`.

## Dataset Creation and Loading

### `ASEAtomsData`

Signature:

```python
ASEAtomsData(
    datapath,
    load_properties=None,
    load_structure=True,
    transforms=None,
    subset_idx=None,
    property_units=None,
    distance_unit=None,
)
```

Use for direct random access to SchNetPack ASE DB rows.

Important behavior:

- `datapath` points to an ASE `.db` file.
- `load_properties=None` loads all properties declared in `_property_unit_dict`.
- `load_properties=[...]` is validated immediately against `available_properties`.
- `load_structure=True` returns atomic numbers, positions, cell, periodic flags, atom count, and row index in addition to properties.
- `property_units` and `distance_unit` request conversion on load; native metadata is unchanged.
- Missing `_distance_unit` or `_property_unit_dict` raises an `AtomsDataError` asking the user to add units.

Common members and methods:

| Member | Purpose |
| --- | --- |
| `len(dataset)` | number of rows, or number of `subset_idx` entries |
| `dataset[i]` | tensor dictionary for one row after transforms |
| `dataset.available_properties` | keys from metadata `_property_unit_dict` |
| `dataset.units` | property-unit dictionary after requested conversions |
| `dataset.metadata` | ASE DB metadata dictionary |
| `dataset.atomrefs` | atom reference tensors converted to requested property units |
| `dataset.subset(indices)` | shallow subset view used by data modules |
| `dataset.iter_properties(...)` | generator for selected rows/properties, optionally with row metadata |
| `dataset.update_metadata(**kwargs)` | add public metadata keys; protected underscore keys are not accepted here |
| `dataset.add_system(atoms=..., **properties)` | append one row |
| `dataset.add_systems(property_list, atoms_list=None, atoms_metadata_list=None)` | append many rows |

### `ASEAtomsData.create`

Signature:

```python
ASEAtomsData.create(
    datapath,
    distance_unit,
    property_unit_dict,
    atomrefs=None,
    **kwargs,
)
```

Creates a new `.db` with SchNetPack metadata and returns an `ASEAtomsData` instance. The file must not already exist. `property_unit_dict` must include every property that will be stored on each row.

### `create_dataset` and `load_dataset`

Signatures:

```python
create_dataset(datapath, format, distance_unit, property_unit_dict, **kwargs)
load_dataset(datapath, format, **kwargs)
```

Use these when code should be format-generic. In SchNetPack 2.2.0 the supported format enum is `AtomsDataFormat.ASE`, mapped to `.db`.

`resolve_format(datapath, format=None)` infers `.db` as ASE. If a path has no suffix and a format is provided, SchNetPack appends the format suffix; if both suffix and format are missing, it raises an error.

## Data Module

Signature:

```python
AtomsDataModule(
    datapath,
    batch_size,
    num_train=None,
    num_val=None,
    num_test=None,
    split_file="split.npz",
    format=None,
    load_properties=None,
    val_batch_size=None,
    test_batch_size=None,
    transforms=None,
    train_transforms=None,
    val_transforms=None,
    test_transforms=None,
    train_sampler_cls=None,
    train_sampler_args=None,
    num_workers=8,
    num_val_workers=None,
    num_test_workers=None,
    property_units=None,
    distance_unit=None,
    data_workdir=None,
    cleanup_workdir_stage="test",
    splitting=None,
    pin_memory=False,
)
```

Lifecycle:

1. Instantiate with data path, split sizes, requested properties, transforms, and unit conversions.
2. Call `prepare_data()` for built-in datasets that download or convert raw data. The base `AtomsDataModule` does not create custom data by itself.
3. Call `setup(stage=None)` to load the dataset, create or load splits, create subset datasets, and attach transforms.
4. Use `train_dataloader()`, `val_dataloader()`, and `test_dataloader()`.
5. Optionally call `teardown(stage)`; if `data_workdir` is set and `stage == cleanup_workdir_stage`, the copied workdir is removed.

Important behavior:

- `val_batch_size` defaults to `test_batch_size` then `batch_size`; `test_batch_size` defaults to `val_batch_size` then `batch_size`.
- `num_val_workers` and `num_test_workers` default to `num_workers` unless overridden.
- Existing `split_file` wins over newly requested split sizes and is validated against non-null requested counts.
- If no split file exists, both `num_train` and `num_val` must be set.
- `data_workdir` copies the DB to a local work directory under a process lock, reloads datasets from the copy, and can clean up on teardown.
- `pin_memory=True` is useful for GPU training but can be `False` for CPU checks.

## Splitting APIs

### `RandomSplit`

Default splitter. Uses random index permutation over the dataset length.

Split size rules:

- Integers are absolute counts.
- Floats below `1` are converted with `floor(size * len(dataset))`.
- One partition can be `None` or negative to receive remaining data.
- More than one undefined partition raises `ValueError`.

### `SubsamplePartitions`

Uses predefined partition arrays stored in dataset metadata, useful for datasets such as `rMD17` with known/test partitions.

Constructor:

```python
SubsamplePartitions(
    split_partition_sources,
    split_id=0,
    base_splitting=None,
    partition_key="splits",
)
```

The number of `split_sizes` must match `split_partition_sources`.

### `GroupSplit`

Splits by group metadata so conformers, stereoisomers, or other related systems do not cross partitions.

Constructor:

```python
GroupSplit(splitting_key, meta_key="groups_ids", dataset_ids_key=None)
```

Requires `dataset.metadata[meta_key][splitting_key]` to align with dataset rows or the current subset.

## Loader and Batch Keys

`AtomsLoader(dataset, batch_size=1, shuffle=False, sampler=None, batch_sampler=None, num_workers=0, collate_fn=_atoms_collate_fn, pin_memory=False, **kwargs)` wraps PyTorch `DataLoader` with SchNetPack collation.

The collate function concatenates per-atom tensors, builds molecule index `idx_m`, offsets neighbor indices across systems, and preserves triple-neighbor indices when present. If neighbor transforms were applied, expect keys such as neighbor pair indices and offsets in addition to standard structure keys.

Common structure keys come from `schnetpack.properties`, including:

- `Z`: atomic numbers.
- `R`: positions.
- `cell`: simulation cell.
- `pbc`: periodic boundary flags.
- `n_atoms`: atom counts per structure.
- `idx`: dataset row index.
- `idx_m`: molecule index per atom in a batch.

## Statistics Helpers

### `calculate_stats`

Signature:

```python
calculate_stats(dataloader, divide_by_atoms, atomref=None)
```

Returns `{property: (mean, stddev)}` computed over the loader. Set `divide_by_atoms={property: True}` for extensive properties when statistics should be per atom. Pass `atomref=dataset.atomrefs` to subtract atom reference contributions before accumulating statistics.

### `estimate_atomrefs`

Signature:

```python
estimate_atomrefs(dataloader, is_extensive, z_max=100)
```

Uses linear regression over element counts and property values to estimate elementwise atomrefs. This is a diagnostic or preparation helper; verify the physical meaning before using generated atomrefs in production.

## Built-in Dataset Constructors

All listed constructors inherit `AtomsDataModule` and accept the common data-module arguments unless noted.

| Class | Required identity args | Special behavior |
| --- | --- | --- |
| `schnetpack.datasets.QM9` | `datapath`, `batch_size` | downloads figshare data if missing; `remove_uncharacterized` validates whether the DB includes excluded molecules |
| `schnetpack.datasets.MD17` | `datapath`, `molecule`, `batch_size` | validates molecule metadata in existing DBs |
| `schnetpack.datasets.rMD17` | `datapath`, `molecule`, `batch_size` | optional `split_id` uses predefined known/test split metadata through `SubsamplePartitions` |
| `schnetpack.datasets.MD22` | `datapath`, `molecule`, `batch_size` | GDML-style larger-molecule data |
| `schnetpack.datasets.ANI1` | `datapath`, `batch_size` | optional `num_heavy_atoms` and `high_energies`; stores energy atomrefs |
| `schnetpack.datasets.ISO17` | `datapath`, `fold`, `batch_size` | `datapath` is a directory; DB path is built from `iso17/<fold>.db` |
| `schnetpack.datasets.QM7X` | `datapath`, `batch_size` | supports raw-data path and filtering flags; properties are limited by class mappings |
| `schnetpack.datasets.MaterialsProject` | `datapath`, `batch_size`, `apikey` when downloading | validates key length and needs optional Materials Project dependencies |
| `schnetpack.datasets.OrganicMaterialsDatabase` | `datapath`, `batch_size`, `raw_path` when converting | requires raw archive when DB is absent |
| `schnetpack.datasets.TMQM` | `datapath`, `batch_size` | downloads/parses tmQM source files if DB is absent |

## Conversion Helper

The bundled helper is intentionally self-contained and runnable from any working directory:

```bash
python sub-skills/data-pipelines/scripts/convert_ase_units.py --help
python sub-skills/data-pipelines/scripts/convert_ase_units.py data.db --distunit Ang --propunit energy:eV,forces:eV/Ang
```

Options:

| Option | Meaning |
| --- | --- |
| `data_path` | ASE DB file to update |
| `--distunit UNIT` | set `_distance_unit`; rejects `A` with a message recommending `Ang`/`Angstrom` |
| `--propunit PROPERTY:UNIT,...` | merge property units into `_property_unit_dict` |
| `--expand-property-dims NAME [NAME ...]` | expand first dimension of selected row data arrays |
| `--dry-run` | print planned metadata and skip writes |
| `--quiet` | reduce progress output |

Make a backup or operate on a copy before editing user data. The helper updates ASE DB metadata in place when not in dry-run mode.
