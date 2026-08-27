# Latency Submission Workflows

## Module contract

A latency challenge image must provide an importable module named `wod_latency_submission` with:

- `initialize_model()`: no arguments; load model state before timed examples.
- `DATA_FIELDS`: list of input field names to load from each example directory. Some documentation uses `DATA_FORMATS`; the evaluator source uses `DATA_FIELDS`.
- `run_model(**data)`: receives numpy arrays named by `DATA_FIELDS` and returns a dictionary containing exactly `boxes`, `scores`, and `classes`.

## Output contract

`boxes` is `N x 7` for 3D detection: center x/y/z, length, width, height, heading. For 2D detection it is `N x 4`: center x/y, length, width. `scores` is length `N` float confidence in `[0, 1]`. `classes` is length `N` uint8/int class ids.

## Evaluator flow

For every `context_name/timestamp_micros` input directory, the evaluator loads the requested `.npy` files, calls `run_model`, saves `boxes.npy`, `scores.npy`, `classes.npy`, and writes `input_fields.txt`. It records elapsed latency per frame in a text file. Full official timing runs in a submitted Docker image; the bundled validator only checks the Python contract.

## Docker image source

Challenge submissions may point to a Docker image tarball in cloud storage or a registry image digest. Use immutable tags/digests and ensure the challenge service account can read the artifact. Keep the image self-contained and make `wod_latency_submission` importable on `PYTHONPATH`.

## Convert latency results

The source conversion script walks `results_dir/context_name/timestamp_micros/`, reads the three `.npy` arrays plus optional `input_fields.txt`, filters invalid objects, and writes an Objects proto. Use `metrics-evaluation` for downstream accuracy scoring.
