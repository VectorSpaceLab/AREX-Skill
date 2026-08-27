---
name: evaluation-and-visualization
description: "Routes Ultra-Fast-Lane-Detection checkpoint evaluation, TuSimple
  scoring, CULane evaluation, and demo visualization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# evaluation-and-visualization

Use this sub-skill when a task is about scoring a trained checkpoint, building or invoking the CULane evaluator, generating TuSimple metrics, or creating the demo video outputs from the repo.

## Read this when

- You need to run `test.py` on CULane or TuSimple.
- You need to score precomputed TuSimple predictions.
- You need to build or call the CULane evaluator binary.
- You need to generate AVI visualizations with `demo.py`.

## What this sub-skill owns

- Evaluation command construction.
- CULane and TuSimple output formats.
- Demo output and visualization behavior.
- CULane evaluator build/run caveats.
- Checkpoint loading and prefix compatibility on evaluation.

## What it does not own

- Training loop mechanics: see `training`.
- Dataset layout and conversion: see `data-and-config`.
- TorchScript export and speed timing: see `export-and-speed`.

## Start here

- Read `references/evaluation-workflows.md` for the practical command patterns.
- Read `references/output-formats.md` for CULane line files and TuSimple JSONL expectations.
- Read `references/visualization.md` when the user wants to inspect the demo output video.
- Read `references/troubleshooting.md` when evaluation or visualization fails.
- Use `scripts/score_tusimple_json.py` to score an existing TuSimple prediction file.
- Use `scripts/run_culane_evaluator.sh` as the safer evaluator launcher.

## Typical flow

1. Confirm the dataset family and checkpoint path.
2. Load the checkpoint with the repo's compatible-state logic.
3. Run the evaluation command or the scoring helper.
4. If the user wants visual output, run the demo workflow separately.
5. If CULane F-measure is required, build the evaluator binary first.

## Caution points

- The repo's evaluation scripts call `.cuda()` directly.
- TuSimple evaluation expects `raw_file`, `lanes`, `h_samples`, and `run_time` in the prediction JSONL.
- CULane scoring depends on a native evaluator binary built from `evaluation/culane/`.
- Demo outputs are written as AVI files and the source script assumes the default repo output naming.

## Reference and script links

- `references/evaluation-workflows.md` for the command patterns and binary requirements.
- `references/output-formats.md` for the file formats.
- `references/visualization.md` for demo behavior and output placement.
- `references/troubleshooting.md` for checkpoint, evaluator, and OpenCV issues.
- `scripts/run_culane_evaluator.sh` for a parameterized evaluator wrapper.
- `scripts/score_tusimple_json.py` for TuSimple JSONL scoring.
