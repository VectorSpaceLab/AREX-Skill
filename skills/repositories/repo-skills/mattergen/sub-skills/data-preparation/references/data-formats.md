# MatterGen dataset formats

Use this reference when deciding whether a released archive, CSV folder, or
cache directory is ready for the package data loader. The converter is the
installed `csv-to-dataset` console entry point; the bundled
[CSV validator](../scripts/validate_dataset_csv.py) only checks inputs and never
creates a cache.

## CSV input contract

`csv-to-dataset` requires `--csv-folder`, `--dataset-name`, and
`--cache-folder`. It enumerates every filename ending in `.csv` in the supplied
folder. A folder containing unrelated CSV files is therefore unsafe: every one
is treated as a split and must satisfy the same structure contract.

The converter reads these columns directly:

| Column | Required | Meaning and handling |
|---|---:|---|
| `cif` | yes | CIF text parsed by pymatgen; the primitive structure is selected. |
| `material_id` | yes | Copied to the structure as its identifier and saved as `structure_id.npy`. |

The source fixture also contains metadata such as `formation_energy_per_atom`,
`band_gap`, `pretty_formula`, `e_above_hull`, `elements`, and
`spacegroup.number`. Do not assume that every such column is used: only columns
whose exact names are in MatterGen's property-source registry are copied by the
converter. Unknown columns are ignored.

The registry at this package version contains these property-source IDs:

- `dft_mag_density`
- `dft_bulk_modulus`
- `dft_shear_modulus`
- `energy_above_hull`
- `formation_energy_per_atom`
- `space_group`
- `hhi_score`
- `ml_bulk_modulus`
- `chemical_system`
- `dft_band_gap`

Pass selected IDs to the validator with repeated `--property NAME` options.
Without that option, it compares all recognized property columns found in the
folder. A recognized property present in one split but absent in another is a
blocking schema error. Blank values are allowed for sparse labels, but an
entirely blank selected column is not useful and is rejected.

CIF parsing follows the converter's behavior: parse the text with
`primitive=True` and `on_error="ignore"`, then use the first parsed structure.
The validator parses rows without writing structures or NumPy arrays. It should
find malformed or empty CIF cells before the expensive converter is launched.

## Cache layout and validation

For ordinary split names, the converter writes each CSV into:

```text
<CACHE_FOLDER>/<DATASET_NAME>/<CSV_STEM>/
```

For example, `train.csv`, `val.csv`, and `test.csv` become sibling split
folders. The package data configs load `train`, `val`, and (for MP-20) `test`
from the dataset root. Keep names simple and unique; the converter derives its
folder from the filename before the extension, so dotted filenames should not
be used as split names.

A complete `CrystalDataset` cache has these core files:

```text
pos.npy
cell.npy
atomic_numbers.npy
num_atoms.npy
structure_id.npy
```

Every cached property is an additional `<property-source-id>.json` file. Its
serialized fields are `values`, `property_source_doc_id`, and optional
`origins`; the number of values must equal the number of structures in
`structure_id.npy`. The core arrays represent primitive, reduced structures:
`pos` stores fractional coordinates, `cell` stores lattice matrices,
`atomic_numbers` is concatenated over structures, and `num_atoms` gives the
per-structure boundaries. The loader slices the atom arrays using
`num_atoms`.

After conversion, inspect each expected split before training. This read-only
cache check does not require a GPU:

```bash
python - <<'PY'
from pathlib import Path
import numpy as np

root = Path("<CACHE_FOLDER>/<DATASET_NAME>")
core = ("pos.npy", "cell.npy", "atomic_numbers.npy", "num_atoms.npy", "structure_id.npy")
for split in ("train", "val", "test"):
    path = root / split
    if not path.exists():
        continue
    missing = [name for name in core if not (path / name).is_file()]
    if missing:
        raise SystemExit(f"{split}: missing {missing}")
    n = len(np.load(path / "structure_id.npy", allow_pickle=False))
    atoms = np.load(path / "num_atoms.npy", allow_pickle=False)
    if len(atoms) != n or int(atoms.sum()) != len(np.load(path / "atomic_numbers.npy", allow_pickle=False)):
        raise SystemExit(f"{split}: inconsistent structure/atom counts")
    print(split, "structures=", n, "properties=", sorted(p.stem for p in path.glob("*.json")))
PY
```

Replace placeholders with generic paths. If a conversion was interrupted,
prefer a fresh cache folder or remove only the affected dataset split after
checking that no required results are shared with another run. The converter
creates directories with `exist_ok=True` and is not a transactional job.
