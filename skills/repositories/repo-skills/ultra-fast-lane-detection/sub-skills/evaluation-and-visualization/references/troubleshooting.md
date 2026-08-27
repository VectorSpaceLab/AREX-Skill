# Troubleshooting

## Purpose

Read this when evaluation, scoring, or visualization fails.

## Checkpoint loading problems

### Symptoms
- `FileNotFoundError` for the checkpoint.
- `Missing key(s)` or `Unexpected key(s)` while loading the checkpoint.
- The model loads only after stripping `module.` prefixes.

### Cause
- The checkpoint came from a different training setup or distributed run.
- The model dimensions do not match the dataset family.

### Recovery
- Confirm the checkpoint path and dataset family.
- Use the repo's compatible-state loading behavior and keep `strict=False` where the source already does that.
- Re-check `griding_num`, `num_lanes`, and `backbone` against the training config.

## TuSimple scoring problems

### Symptoms
- The scorer rejects the prediction file.
- `bench_one_submit` complains about missing `raw_file`, `lanes`, or `run_time`.
- The prediction count does not match the ground-truth count.

### Cause
- The JSONL schema is wrong or incomplete.
- The file was generated with a different sample order.

### Recovery
- Compare the file to `references/output-formats.md`.
- Score only predictions produced for the exact TuSimple test set.

## CULane evaluator issues

### Symptoms
- The evaluator binary is missing.
- `cmake` or `make` fails inside `evaluation/culane/`.
- The final metric step cannot find the `evaluate` binary.

### Cause
- OpenCV C++ headers or libraries are not installed.
- The C++ toolchain is not available or the host cannot build the native helper.

### Recovery
- Build the evaluator with the repo's documented commands.
- If the host cannot provide the toolchain, keep the evaluation guidance but mark the CULane score as unverified.

## Demo visualization issues

### Symptoms
- AVI files are not created.
- The output appears in the wrong directory.
- The visualization opens but the frame order looks odd for TuSimple.

### Cause
- The script was run from a surprising working directory.
- The user expected TuSimple to behave like a video dataset.

### Recovery
- Run the demo from a directory where you want the AVI outputs.
- Use the visualization only for qualitative inspection.

## CUDA-only script failures

### Symptoms
- `CUDA not available` or `.cuda()` errors.

### Cause
- The environment does not have a working GPU runtime.

### Recovery
- Do not claim the evaluation flow is fully verified on CPU when the source script uses CUDA directly.
- Ask for a CUDA-capable environment or narrow the request to CPU-safe inspection only.
