# Data-preparation troubleshooting

## Fast triage

1. Confirm the selected loader and `DATA_PATH` layout, not merely the dataset name.
2. Confirm `DO_PREPROCESS`, `CACHED_PATH`, `FILE_LIST_PATH`, `BEGIN < END`, and
   `DATA_FORMAT` are consistent.
3. Run the read-only validator against the CSV or cache directories.
4. Inspect one failing raw source and one generated pair; do not rerun a full build
   until the failure is understood.

## Common failures

### `data paths empty!` / empty raw discovery
The loader's glob pattern did not match the configured root. Check one level above
or below the expected root, case-sensitive names, and dataset-specific nesting.
PURE needs `ii-jj/ii-jj/*.png` and JSON; UBFC-rPPG needs `subject*/vid.avi` and
`ground_truth.txt`; iBVP needs `pNN_x` directories; PhysDrive needs session
`Align` and `Label`; SUMS/LADH need their exact video filename suffixes. Do not
paper over a missing tree with an empty custom CSV.

### Missing or mismatched label
Standard loading derives a label path by replacing `input` with `label`. Check
that the source id and chunk number match exactly and that no unrelated filename
contains the token `input`. For custom lists, the CSV must contain `input_files`,
not a display name. If the input is BigSmall pickle, use its loader-aware load path;
the NPY validator intentionally does not open pickle files.

### `Unsupported data type!` / `Unsupported label type!`
Use only `Raw`, `DiffNormalized`, and `Standardized`, with exact capitalization.
A list may contain multiple video types, which are concatenated along channels;
labels take one label type. Remember that temporal differencing reduces the
intermediate sequence by one and appends a zero frame, so it still ends at `D`.

### Frame/label length mismatch
Check reader-specific synchronization. PURE, UBFC-Phys, MMPD, BP4D+, iBVP,
PhysDrive, LADH, SUMS, and COHFACE resample or interpolate in their workers, while
bad source metadata may still produce empty or malformed arrays. iBVP removes
low-SQ2 frames after resampling; PhysDrive can remove all low-quality clips.
Pseudo labels use the frame sequence and should not be paired with a different
video. Stop if the validator reports a length mismatch.

### No face / strange crop / black output
HC reports no detection and falls back to a full-frame box; multiple faces select
the largest. Verify RGB/BGR conversion and inspect the first frame. Try a smaller
or larger face box, dynamic detection, or a median box according to the motion
pattern. Ensure the crop box has nonzero intersection with the frame. For Y5F,
verify the packaged YAML/checkpoint and device; do not download resources during a
run. The source HC path is relative to the working directory, so a portable
runtime must resolve the cascade resource explicitly and confirm
`CascadeClassifier.empty()` is false.

### Cache exists but list is missing/empty
With preprocessing disabled, the loader may attempt retroactive reconstruction
from raw source ids and `<id>_input*.npy`. This fails after cache relocation or
source-id changes. Supply an explicit CSV, update its paths, and validate it.
`BaseLoader.build_file_list` also raises when no worker returned files; inspect
worker errors rather than creating an empty CSV.

### Motion mode rejects input
Only selected loaders implement a `Motion` branch. Confirm the external augmented
folder contains NPY data where that loader globs it. `read_npy_video` accepts
integer `[0,255]` or floating `[0,1]` frames and takes the first three channels;
other ranges/dtypes raise. Use `DATA_AUG: ['None']` for ordinary AVI/PNG/MAT
inputs.

### MMPD filter removes everything
MMPD parses metadata embedded in cache filenames and applies `INFO` filters.
Check exact numeric encodings for light, motion, exercise, skin color, gender,
glasses, hair cover, and makeup. Unsupported raw strings raise before caching; a
valid cache can still be filtered to zero records. Relax the filter or regenerate
with the intended metadata selection.

### BigSmall fold or shape confusion
Use a fold CSV with a `subjects` column and set the fold path/name together. The
BigSmall loader only uses `T1/T6/T7/T8` and writes pickle inputs containing big and
small arrays plus 49-column labels. Do not expect standard `*_input*.npy` inputs or
use the generic validator on those pickle files.

### Out of memory / run appears hung
Video decoding, face detection, POS pseudo labels, and each multiprocessing worker
hold sizable arrays. Lower the worker quota (the common manager defaults to eight),
use a small probe split, reduce crop size only if the experiment permits, and
process datasets sequentially. Avoid repeated retries while workers still hold
memory. Writes are not transactional; inspect for incomplete pairs before reusing
a partially failed cache.

## Validator exit meanings

The validator exits `0` only when every discovered/listed pair satisfies the
requested shape, numeric dtype, finite-value, and temporal-length checks. It exits
nonzero for missing files, malformed CSVs, unsupported rank/layout, nonnumeric or
nonfinite arrays, or an empty selection. It never repairs, deletes, or rewrites
files.
