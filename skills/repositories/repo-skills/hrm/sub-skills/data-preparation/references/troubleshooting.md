# Data Preparation Troubleshooting

## Builder cannot find ARC raw data

Symptoms:

- `FileNotFoundError` for `dataset/raw-data/ARC-AGI/data`, `ConceptARC/corpus`,
  or `ARC-AGI-2/data`.
- ARC builder prints zero puzzles or fails while scanning subdirectories.

Likely causes:

- Git submodules were not initialized.
- The checkout used SSH submodule URLs without credentials.
- The user supplied the wrong `--dataset-dirs` path.

Recovery:

1. Confirm that the requested raw-data directory exists and contains ARC JSON
   files under task split directories.
2. If network/credentials are allowed, initialize submodules or provide an
   equivalent local ARC data directory.
3. Re-run `python dataset/build_arc_dataset.py --help` to verify option syntax.
4. Use `--dataset-dirs <path>` explicitly rather than relying on defaults when
   using ARC-2 or custom raw data.

## Hugging Face dataset download fails

Symptoms:

- `hf_hub_download` errors, HTTP failures, cache permission errors, or missing
  `train.csv` / `test.csv`.

Likely causes:

- No network, blocked Hugging Face access, bad `--source-repo`, or cache write
  permissions.

Recovery:

1. Verify `--source-repo`; defaults are `sapientinc/sudoku-extreme` and
   `sapientinc/maze-30x30-hard-1k`.
2. If offline, do not keep retrying conversion. Ask for local CSVs or network
   authorization.
3. After conversion succeeds, validate the output layout with the bundled
   validator before training.

## `PuzzleDataset` yields no training batches

Symptoms:

- Training loop appears to skip a split.
- Tiny fixture tests raise `StopIteration` for train mode.

Likely causes:

- `global_batch_size` is larger than the number of examples sampled from a
  group; the loader drops short final training batches.
- `group_indices` or `puzzle_indices` do not cover all puzzles/examples.

Recovery:

1. Run `validate_dataset_layout.py` to catch broken offsets.
2. For tiny smoke fixtures, ensure at least one sampled group can fill
   `global_batch_size`.
3. For real training, set `global_batch_size` to a value supported by the
   dataset and GPU count.

## Token range or metadata mismatch

Symptoms:

- Validator reports inputs/labels outside `[0, vocab_size)`.
- Model loss fails with gather/index errors.
- `seq_len` mismatch between metadata and arrays.

Likely causes:

- Mixed dataset roots, partially overwritten output directory, custom builder
  bug, or wrong token offset for the task family.

Recovery:

1. Delete or move the incomplete output directory before rebuilding.
2. Rebuild one dataset family into a fresh `--output-dir`.
3. Validate both train and test splits.
4. Check task-specific encoding in `data-formats.md`.

## Visualizer does not load files

Symptoms:

- Browser alert says `Missing file: identifiers.json` or a specific `.npy`.
- Grid renders with unexpected colors or sizes.

Likely causes:

- Selected the wrong folder level.
- Missing subset files.
- Browser file API did not preserve relative paths.

Recovery:

1. Select the dataset root folder that directly contains `identifiers.json` and
   split subdirectories.
2. Run the validator on the same folder.
3. Ensure the bundled visualizer's `assets/npyjs.js` file remains adjacent to
   the HTML under `scripts/assets/`.
