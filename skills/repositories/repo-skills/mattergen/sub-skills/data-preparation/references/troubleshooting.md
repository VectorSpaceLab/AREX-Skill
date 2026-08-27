# Data-preparation troubleshooting

## Install and import failures

- Start with `csv-to-dataset --help`. If the console entry point is absent,
  activate the environment where MatterGen was installed and retry; an editable
  install is the documented setup. The module fallback is
  `python -m mattergen.scripts.csv_to_dataset --help`.
- The converter imports the MatterGen dataset stack, NumPy, pandas, tqdm,
  pymatgen, PyTorch, and PyTorch Geometric. A CUDA device is not needed merely
  to parse CSV/CIF data, but mismatched PyTorch/PyG wheels can prevent the
  package import before conversion starts. Repair the environment rather than
  bypassing the package loader.
- For this inspected release, the verified inspection environment used Python
  3.10, torch 2.2.1+cu118, torch_geometric 2.8.0.post1, CUDA PyG extension
  wheels, and pymatgen 2024.10.29. Treat those as evidence for that environment,
  not universal requirements. On Apple Silicon, training has separate MPS
  guidance; conversion remains a CPU-oriented task.
- `validate_dataset_csv.py --help` uses only the standard library. A normal run
  additionally needs the installed MatterGen property registry and pymatgen
  CIF parser. It exits with a blocking diagnostic if either cannot be loaded.

## LFS, archive, and storage failures

- If `unzip` reports that an archive is not a ZIP, check whether the file is an
  LFS pointer. Install/configure Git LFS and explicitly pull the required
  MP-20 or Alex-MP-20 path; do not assume a clone fetched large objects.
- Download and unzip are opt-in workflow steps. The validator never downloads,
  unpacks, converts, or writes cache data.
- A killed job, `No space left on device`, or a long-running Alex-MP-20 job is
  not evidence of a valid cache. Use `df -h`, inspect the generated split, and
  rerun into a fresh cache location after fixing capacity. Do not train from a
  split with missing core files or an uncertain partial write.

## CSV and CIF validation

- `missing required column(s)` means the exact lowercase `cif` or
  `material_id` header is absent. Similar-looking fields (`id`, `structure`, or
  `structure_id`) are not accepted by the package converter.
- `CIF parse failed` or `CIF parser returned no structures` identifies a row
  that the package converter would not turn into its first primitive structure.
  Inspect quoting and multiline CIF fields; do not replace malformed structures
  with a placeholder.
- The validator sorts `.csv` filenames and checks every one. Keep archives,
  notes, and unrelated CSV measurements outside the input folder.
- A property missing from one split is a schema error when it is selected with
  `--property` or recognized in another split. Partial blanks are reported as a
  warning because `filter_sparse_properties` can remove those structures when
  the property is selected. An all-blank selected property is a blocking error.
- `space_group` values must be symbols accepted by pymatgen. A source column
  named `spacegroup.number` is not the same property ID and is ignored by the
  converter unless the dataset was explicitly transformed before this workflow.

## CLI, config, and cache misuse

- All three converter options are required: `--csv-folder`, `--dataset-name`,
  and `--cache-folder`. The source function contains a default for
  `--cache-folder`, but `required=True` means callers must still provide it.
- `--csv-folder` is a folder, not a single CSV path. `--dataset-name` is the
  logical cache directory name, not a path to a CSV. The converter processes
  every `.csv` in the folder and writes one split directory per filename stem.
- If training cannot find `train`, `val`, or `test`, compare the actual cache
  tree with the selected data-module config. MP-20 config expects all three;
  Alex-MP-20 config expects train and val. Override `data_module.root_dir` when
  the cache was placed outside the package default.
- If a selected property is unavailable, check both its exact registry name and
  its `<property>.json` cache file. Adding a CSV column without registering the
  name or configuring its embedding does not enable fine-tuning.
- A previous conversion can leave old JSON files in an existing split because
  the converter reuses directories. Use a new cache location or clean the
  affected split deliberately, then rerun the cache check in
  [data-formats](data-formats.md).

## Workflow and scientific limits

- A preflight pass proves input shape and parseability, not that energies,
  property units, IDs, or train/validation leakage are scientifically correct.
  Keep source version, preprocessing modifications, label provenance, and
  license records with the experiment.
- MP-20 is documented as CC BY 4.0, and Alex-MP cites the Alexandria CC BY 4.0
  release plus its MP-20 component. The repository's MIT code license does not
  replace the dataset licenses. Preserve attribution and each release's stated
  modifications when redistributing or publishing derivatives.
- Released training data excludes Tc, Pm, and elements with atomic number 84 or
  higher; MP-20 is capped at 20 atoms and Alex-MP-20 applies the documented
  20-atom and energy-above-hull filters. A successful custom CSV conversion does
  not prove those scientific filters hold.
- If a requested task needs a new schema, source download, DFT relabeling, or
  an unsupported property embedding, stop at this sub-skill and hand off the
  unresolved requirement instead of guessing.
