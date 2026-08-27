---
name: data-preparation
description: "Prepare and validate MatterGen crystal CSV data, released MP-20 or
  Alex-MP-20 archives, cache splits, and custom property labels before training,
  fine-tuning, or evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MatterGen data preparation

Use this sub-skill when a MatterGen workflow needs a released MP-20 or
Alex-MP-20 dataset, CSV-to-cache preprocessing, a custom property column, or a
preflight before training/fine-tuning/evaluation. The parent MatterGen skill
should route here before invoking a trainer or property adapter.

This is a preparation and validation route, not a downloader, data scientist,
or model-quality evaluator. It does not silently fetch LFS objects, unzip
archives, convert data, repair malformed CIFs, invent columns, or import
unverified caches.

## Fast route

1. Identify the dataset source, version, split names, property labels, storage
   location, and license/provenance record. Keep the CSV folder limited to the
   splits intended for this run.
2. Check available storage before downloading or unzipping a large release.
   Alex-MP-20 preprocessing is documented as taking about an hour and may need
   archive, extracted CSV, and cache space at the same time.
3. Run the safe, read-only [CSV preflight script](scripts/validate_dataset_csv.py)
   over the complete CSV folder. Add one `--property NAME` for every selected
   label. Use `--limit-rows` only for a preliminary probe, never as the final
   gate.
4. Resolve every `ERROR`, review `WARN` output for sparse labels, and rerun the
   full preflight. A pass means the package converter can be attempted; it does
   not prove scientific correctness or label comparability.
5. Run the actual `csv-to-dataset` package CLI with all three required options.
   It processes every `.csv` in the folder and writes one cache directory per
   filename stem. It is not the same operation as the bundled validator.
6. Inspect the generated core arrays and property JSON files using the cache
   check in [data formats](references/data-formats.md). Use a fresh cache root
   after interruption or schema changes.
7. Point the selected data-module config at the verified dataset root, then
   hand off to training/fine-tuning/evaluation with the provenance and
   unresolved limits recorded.

## Exact input and output contract

The converter consumes CSV rows with exact lowercase `cif` and `material_id`
columns. `cif` is parsed into a primitive pymatgen structure; `material_id`
becomes the structure identifier. The converter copies only exact property IDs
registered by the installed MatterGen package. Similar names such as
`band_gap`, `e_above_hull`, or `spacegroup.number` are not silently mapped.

For a folder containing ordinary `train.csv`, `val.csv`, and `test.csv`, the
logical output is:

```text
<CACHE_FOLDER>/<DATASET_NAME>/train/
<CACHE_FOLDER>/<DATASET_NAME>/val/
<CACHE_FOLDER>/<DATASET_NAME>/test/
```

The required core cache files are `pos.npy`, `cell.npy`,
`atomic_numbers.npy`, `num_atoms.npy`, and `structure_id.npy`. Registered
properties are written as `<property>.json`. See [data formats](references/data-formats.md)
for array semantics, split expectations, recognized property IDs, and a
read-only cache validation command.

The package data configs use these split contracts:

- `mp_20`: `train`, `val`, and `test`; default properties are empty and common
  supported labels are documented in its data-module config.
- `alex_mp_20`: `train` and `val`; default properties are empty and the config
  also documents `ml_bulk_modulus`, `hhi_score`, `space_group`, and
  `energy_above_hull`.

Both configs apply lattice symmetrization and set a chemical-system string as a
sample transform. Both apply `filter_sparse_properties` as a dataset transform;
when properties are selected, rows missing any selected value are filtered.

## Released data route

MP-20 and Alex-MP-20 are separate training releases. Download and unzip only
with explicit user approval. The documented commands and storage-aware route
are in [released-data workflows](references/workflows.md). Use a user-supplied
release archive or hydrated download; the skill does not assume a particular
checkout layout. In summary, the normal sequence is:

```bash
# Explicitly acquire and verify <MP20_ARCHIVE>.zip first.
unzip <MP20_ARCHIVE>.zip -d <DATA_ROOT>
python <mattergen-skill-root>/sub-skills/data-preparation/scripts/validate_dataset_csv.py \
  --csv-folder <DATA_ROOT>/mp_20
csv-to-dataset --csv-folder <DATA_ROOT>/mp_20 \
  --dataset-name mp_20 --cache-folder <CACHE_ROOT>
```

For Alex-MP-20, substitute the user-supplied archive and extracted folder:

```bash
unzip <ALEX_MP20_ARCHIVE>.zip -d <DATA_ROOT>
python <mattergen-skill-root>/sub-skills/data-preparation/scripts/validate_dataset_csv.py \
  --csv-folder <DATA_ROOT>/alex_mp_20
csv-to-dataset --csv-folder <DATA_ROOT>/alex_mp_20 \
  --dataset-name alex_mp_20 --cache-folder <CACHE_ROOT>
```

If the archive is stored in Git LFS, hydrate only the explicitly requested
release object using the user's checkout-aware command, then verify that the
result is a real ZIP rather than an LFS pointer before extraction.

Run the bundled validator between extraction and conversion. An LFS pointer is
not a ZIP. Do not download the Alex-MP reference energy archives, presentation
CIF archive, or measurement files for this training-data route.

## Custom properties and split discipline

For an existing property, pass its exact registry name to the validator and
place the same column in every relevant CSV split. Sparse labels may be
intentional, but an entirely blank selected column or a missing column in one
split is a blocking preparation problem.

For a new property, register its exact name in MatterGen's property-source
registry before conversion, add the column, rebuild the cache, add a compatible
property-embedding configuration, and select it in the data module. A column
that merely passes CSV parsing will otherwise be ignored by the converter.
Read [custom properties](references/custom-properties.md) for the supported
value/provenance rules and fine-tuning handoff.

## Storage, config, and handoff

Before Alex-MP-20, use `df -h` and `du -sh` on the archive, extracted CSV, and
intended cache locations. If disk is constrained, place `--cache-folder` on a
larger filesystem and override `data_module.root_dir` to the resulting
`<CACHE_FOLDER>/<DATASET_NAME>` before training. Do not launch a full
conversion merely to discover that the cache destination is too small.

The package CLI is CPU-oriented for parsing, although its import stack includes
PyTorch and PyTorch Geometric. GPU/backend compatibility matters later for
training and diffusion data utilities, not for the safe preflight itself. Use
`csv-to-dataset --help` and the [troubleshooting guide](references/troubleshooting.md)
for import, optional-backend, LFS, CLI, config, cache, and workflow failures.

Record the dataset release/source version, citations and CC BY 4.0 obligations,
repository preprocessing modifications, property units and calculation
method, split/ID policy, command parameters, cache location, and validation
result outside this runtime tree. The code is MIT-licensed, but that does not
replace the separate MP-20/Alexandria dataset terms.

## Verification gates

A data-preparation handoff is ready only when:

- `csv-to-dataset --help` succeeds in the intended environment;
- the full validator exits zero, or all warnings are explicitly accepted;
- every intended split has the five core arrays and matching structure/atom
  counts;
- every selected property JSON exists and has one value per structure;
- the configured data-module split paths resolve to those caches; and
- provenance, licensing, storage decisions, and unresolved scientific limits
  are recorded.

If conversion is interrupted, a required dependency is broken, a CIF cannot be
parsed, a selected property schema differs across splits, or a cache check
fails, stop and route through [troubleshooting](references/troubleshooting.md).
Do not claim that training or fine-tuning is ready.
