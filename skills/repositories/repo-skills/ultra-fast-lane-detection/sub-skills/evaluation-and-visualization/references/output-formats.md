# Output Formats

## Purpose

Read this when you need to understand the files written by evaluation or demo runs.

## CULane line files

The CULane evaluation path writes `lines.txt` files under the work directory.

- Each line contains a predicted lane as pairs of x/y coordinates.
- The evaluator expects the split layout from `list/test_split/`.
- The final metric step reads those generated line files and compares them with the dataset annotations.

## TuSimple JSONL output

Each prediction row is a JSON object with these keys:

- `lanes`
- `h_samples`
- `raw_file`
- `run_time`

### `lanes`

- A list of lane coordinate sequences.
- Missing points use `-2` in the TuSimple protocol.

### `h_samples`

- The vertical sample positions used for the TuSimple benchmark.
- The repo uses the canonical TuSimple list of sample heights.

### `raw_file`

- The original sample name from the dataset.
- Must match the ground-truth file names in `test_label.json`.

### `run_time`

- The per-sample runtime recorded by the benchmark file.

## Demo AVI output

- `demo.py` writes AVI files in the current working directory unless the user runs it from a different directory.
- The script names the output after the split being processed.
- The visualization overlays lane points on the original frame.

## Why these formats matter

- TuSimple scoring rejects files that do not match the JSONL schema.
- CULane scoring rejects line files that do not match the evaluator's coordinate expectations.
- The demo output is not a metric file; it is for visual inspection only.
