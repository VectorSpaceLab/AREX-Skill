# Evaluation data formats

## Structure input

`--structures_path` must point to:

1. `.xyz` or `.extxyz`: ASE reads all frames in file order;
2. `.zip`: a trusted archive whose supported files are available at the
   extracted top level; the package extracts it to a temporary directory and
   processes those supported files;
3. a directory: direct files are processed in `os.listdir` order.

Supported directory suffixes are lowercase `.cif`, `.xyz`, and `.extxyz`.
CIFs are read as pymatgen structures. Directory XYZ/EXTXYZ files are read only
at frame 0; use one structure per such file. A multi-frame top-level EXTXYZ is
the least ambiguous way to preserve one-to-one ordering.

Keep the original sample manifest. Filenames, ZIP member order, and filesystem
order are not stable identifiers across copies or operating systems.

## Precomputed energy array

`--energies_path` is loaded by `numpy.load`, normally from a `.npy` file. It
must be numeric, finite, one-dimensional, and have exactly one **total energy**
for every loaded structure, in exactly the loader's order. Energies are not
per-atom values; MatterGen constructs `ComputedStructureEntry` objects and
pymatgen derives per-atom hull values.

The safe adapter rejects a missing array in `relax=False`, extra dimensions,
non-numeric values, non-finite values, or count mismatch. It rejects any array
in `relax=True`. If the calculator emitted per-atom energies, convert them to
total energies using the same structure atom counts before evaluation and
record that conversion.

## Reference dataset

The CLI expects a path to gzip-compressed LMDB written by
`LMDBGZSerializer`. The reference consists of `ComputedStructureEntry` objects
with structure, total energy, run metadata, and correction adjustments. The
serializer stores a dataset name, chemical-system and reduced-formula indexes,
and entries. It is lazy on deserialize, but matching and hull metrics can still
be expensive.

The repository provides Alex-MP reference assets for MP2020 and TRI2024 under
its data-release area. They are large Git LFS assets; the evaluation wrapper
requires an existing local path and does not fetch them.

A custom reference can be constructed from entries:

```python
from mattergen.evaluation.reference.reference_dataset import ReferenceDataset
from mattergen.evaluation.reference.reference_dataset_serializer import LMDBGZSerializer

ref = ReferenceDataset.from_entries("custom", entries)
LMDBGZSerializer().serialize(ref, "custom.gz")
```

When creating entries from raw PBE/GGA energies, use `VasprunLike` and apply
one correction scheme consistently. MP2020 and TRI2024 entries are not
interchangeable. Custom datasets produce a warning about compatibility; this
is an explicit user responsibility.

## Output formats

- `save_as`: JSON mapping metric names to objects containing `value` and
  `description` (the source `MetricsEvaluator.compute_metrics` writes the
  detailed metric records). The Python return value and console JSON reduce
  these records to `{name: value}` scalars. Inspect the saved file rather than
  assuming it has the console shape.
- `save_detailed_as`: a Monty-serialized pandas table containing per-entry
  aggregates and capability data. It is intended for analysis and includes
  values such as `energy_above_hull`,
  `self_consistent_energy_above_hull`, `stable`, `novel`, `unique`, and
  optional `rmsd_from_relaxation`.
- `structures_output_path`: EXTXYZ written by MatterSim relaxation. It may
  include final positions, total energy, forces, and stresses. This file is
  not produced in no-relax mode.

## Correction and energy semantics

MP2020 is pymatgen's `MaterialsProject2020Compatibility`; it is the default
for input entries and default reference selection. TRI2024 is MatterGen's
`TRI110Compatibility2024`, with a PBE scaling correction and element-specific
GGA+U adjustments. The correction object processes input entries; the
reference must have been processed under the same convention.

Stability is based on energy above a reference convex hull, with the default
threshold `0.1 eV/atom`. Self-consistent energy above hull adds sampled entries
to the hull. A missing terminal system or missing finite terminal energy can
prevent energy metrics even when structure metrics are available.
