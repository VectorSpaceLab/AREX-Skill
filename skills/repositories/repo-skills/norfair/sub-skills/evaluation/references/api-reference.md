# Norfair evaluation API reference

This reference captures the source-evidenced behavior of Norfair's MOTChallenge evaluation helpers without requiring the source demo tree.

## MOTChallenge layout expectations

Use a MOTChallenge `train/` split when you want scores. The `test/` split does not provide labels, so it cannot be used for ground-truth evaluation with `eval_motChallenge`.

Typical sequence layout:

```text
MOT17/train/MOT17-02-FRCNN/
  seqinfo.ini
  gt/gt.txt
  det/det.txt
```

Typical output layout used by the bundled helpers:

```text
<output-root>/predictions/MOT17-02-FRCNN.txt
<output-root>/metrics.txt
```

Layout notes:

- `seqinfo.ini` must contain plain `key=value` lines. The evaluation helpers rely on `seqLength`.
- `gt/gt.txt` is the ground-truth MOTChallenge file loaded by `eval_motChallenge`.
- `det/det.txt` is the detection file parsed by `DetectionFileParser`.
- Saved predictions follow the MOTChallenge text layout written by `PredictionsTextFile`.
- Sequence names are matched by the sequence folder basename. Keep ground-truth and prediction names aligned.

## `InformationFile`

Constructor:

```python
InformationFile(file_path)
```

Purpose:

- Read a `seqinfo.ini` file into memory.
- Provide a minimal lookup helper for MOTChallenge-style metadata.

Key behavior:

- `search(variable_name)` scans lines in order and returns the value for the first line that starts with the requested key.
- If the value is composed only of digits, `search` returns an `int`.
- Otherwise it returns the raw string.
- If the key is missing, `search` raises `ValueError`.

Important caveats:

- The parser expects plain `key=value` formatting. Extra spaces around the equals sign can cause `search` to return a string instead of an integer.
- `seqLength` must be parseable as a plain integer because the evaluation helpers use it for frame iteration.

## `PredictionsTextFile`

Constructor:

```python
PredictionsTextFile(input_path, save_path=".", information_file=None)
```

Purpose:

- Create a MOTChallenge prediction text file for one sequence.
- Write tracked objects in the standard MOTChallenge box format while a tracker loop runs.

Default file location:

```text
<save_path>/predictions/<sequence-name>.txt
```

Sequence name is taken from the basename of `input_path`.

Key behavior:

- If `information_file` is not provided, the class reads `seqinfo.ini` from the sequence folder.
- It reads `seqLength` from the sequence metadata and closes the file after the last expected frame.
- `update(predictions, frame_number=None)` writes one row per tracked object in this format:

```text
frame_number,id,bb_left,bb_top,bb_width,bb_height,-1,-1,-1,-1
```

- Each prediction object must expose `id` and `estimate`, where `estimate` is a 2x2 corner array.

Operational notes:

- Call `update` once per frame.
- If you stop a run early, close the underlying file handle yourself; the class only auto-closes after `seqLength` frames.

## `DetectionFileParser`

Constructor:

```python
DetectionFileParser(input_path, information_file=None)
```

Purpose:

- Load MOTChallenge detections from `det/det.txt`.
- Return Norfair `Detection` objects frame by frame.

Expected detection file layout:

```text
<sequence>/det/det.txt
```

Source behavior:

- Reads the full detection matrix with `numpy.loadtxt`.
- Sorts rows by frame number.
- Converts width/height into bottom-right coordinates in place.
- Precomputes one list of `Detection` objects per frame from `1` through `seqLength`.

Each returned `Detection` uses:

- `points = [[x1, y1], [x2, y2]]`
- `scores = [conf, conf]`

Important caveats:

- The detection file must follow the expected 10-column MOTChallenge detection layout.
- Missing files, empty files, or bad column counts fail before evaluation starts.

## `Accumulators`

Purpose:

- Collect tracker outputs for one or more sequences.
- Convert them into the prediction matrices consumed by `eval_motChallenge`.
- Compute and save MOTChallenge summary output.

Key methods:

### `create_accumulator(input_path, information_file=None)`

- Checks that `motmetrics` is available through `mm.metrics`.
- Stores the sequence path.
- Initializes a fresh prediction matrix for that sequence.
- Uses `seqLength` to set up the per-frame progress iterator.

### `update(predictions=None)`

- Expects one call per frame.
- Converts each tracked object into one MOTChallenge row:

```text
frame,id,bb_left,bb_top,bb_width,bb_height,-1,-1,-1,-1
```

- Appends the finished matrix when the internal progress iterator is exhausted.

### `compute_metrics(metrics=None, generate_overall=True)`

- Calls `eval_motChallenge` with the collected prediction matrices and stored paths.
- Defaults to `mm.metrics.motchallenge_metrics`.
- Stores both `summary_text` and `summary_dataframe` on the instance.

### `save_metrics(save_path=".", file_name="metrics.txt")`

- Writes the stored rendered summary text.
- Does not recompute metrics.

### `print_metrics()`

- Prints the stored summary text.

Operational notes:

- `Accumulators` is meant for full-sequence loops. If you skip the final frame, the sequence may never be finalized.
- The object contract is simple: each prediction must expose `id` and `estimate`.

## `load_motchallenge(matrix_data, min_confidence=-1)`

Purpose:

- Convert a MOTChallenge-style row matrix into the `pandas.DataFrame` shape expected by `motmetrics`.

Expected row shape:

```text
[FrameId, Id, X, Y, Width, Height, Confidence, ClassId, Visibility, unused]
```

Key behavior:

- Sets the DataFrame index to `("FrameId", "Id")`.
- Subtracts 1 from `X` and `Y` to account for MATLAB-style coordinate conventions.
- Drops the trailing `unused` column.
- Filters out rows with `Confidence < min_confidence`.

Important caveats:

- Ground truth normally uses `min_confidence=1` so invalid rows are excluded.
- Predictions generally use the default threshold unless you want to filter them yourself first.

## `compare_dataframes(gts, ts)`

Purpose:

- Build `motmetrics` accumulators for each sequence present in both dictionaries.

Key behavior:

- Iterates through the prediction dictionary.
- Only compares keys that also exist in the ground-truth dictionary.
- Uses `mm.utils.compare_to_groundtruth(..., "iou", distth=0.5)`.

Return value:

- A pair: `(accumulators, sequence_names)`.

Important caveat:

- Unmatched sequence names are ignored, so always inspect the matched list before trusting the score.

## `eval_motChallenge(matrixes_predictions, paths, metrics=None, generate_overall=True)`

Purpose:

- Load MOTChallenge ground truth from sequence folders.
- Convert prediction matrices into `motmetrics` DataFrames.
- Compute the rendered MOTChallenge summary table.

Source behavior:

- Loads each `gt/gt.txt` through `mm.io.loadtxt(..., fmt="mot15-2D", min_confidence=1)`.
- Loads each prediction matrix through `load_motchallenge`.
- Uses `compare_dataframes` to build per-sequence accumulators.
- Creates a metrics handler with `mm.metrics.create()`.
- Sets `mm.lap.default_solver = "scipy"` before computing.
- Calls `mh.compute_many(..., generate_overall=generate_overall)`.
- Renders the summary with `mm.io.render_summary(..., namemap=mm.io.motchallenge_metric_names)`.

Return value:

- `summary_text`
- `summary_dataframe`

Important caveats:

- The `paths` list and `matrixes_predictions` list must align by index.
- The function keys ground-truth and predictions by sequence folder basename.
- If you want a subset, filter the sequence list before calling the helper.

## XYAH and ByteTrack-style notes

The source evidence included two variants, but they are not the core runtime contract for this sub-skill:

- A Norfair XYAH variant converts boxes into a ByteTrack-style `[center_x, center_y, aspect_ratio, height]` state before tracking, then converts tracked objects back to MOTChallenge box rows for evaluation.
- A ByteTrack comparison variant converts external ByteTrack tracker outputs into MOTChallenge box rows before scoring.

Use these as conceptual comparison notes when you want to understand how Norfair results line up with ByteTrack-style evaluation logic. Keep the reusable helper focused on MOTChallenge parsing, accumulation, and metrics, and do not make the source demo tree a runtime dependency.