# Evaluation Workflows

## Purpose

Read this when you need to turn a checkpoint into scores or visual outputs.

## Verified entry points

- `test.py` is the main evaluation script.
- `evaluation/eval_wrapper.py` contains the shared logic for CULane and TuSimple evaluation.
- `evaluation/tusimple/lane.py` contains the TuSimple benchmarking helper.
- `demo.py` generates visual AVI output with the predicted lanes overlaid on frames.

## CULane evaluation pattern

1. Load the checkpoint.
2. Generate lane line files under the work directory.
3. Run the CULane evaluator binary built from `evaluation/culane/`.
4. Aggregate the split metrics into the final F-measure style report.

The repo's workflow uses the split files under `list/test_split/` and writes evaluation output into a work directory.

## TuSimple evaluation pattern

1. Load the checkpoint.
2. Generate a prediction JSONL file with one row per test sample.
3. Combine the per-rank outputs if running distributed.
4. Call `LaneEval.bench_one_submit(pred_file, gt_file)` to get the benchmark JSON.

## Demo pattern

- `demo.py` loads a checkpoint and writes an AVI for each selected test split.
- The script uses the same lane post-processing logic as the evaluation code, but the output is a video rather than a metric file.

## Command examples

```bash
python test.py configs/culane.py --test_model <CULANE_CKPT> --test_work_dir <WORK_DIR>
python test.py configs/tusimple.py --test_model <TUSIMPLE_CKPT> --test_work_dir <WORK_DIR>
python demo.py configs/culane.py --test_model <CULANE_CKPT>
```

## Binary requirement for CULane

- The CULane evaluator is a separate native binary, not a Python module.
- Build it before asking for the final CULane score.
- If the binary is missing, the evaluation code cannot complete the CULane metric run.

## Checkpoint loading behavior

- The evaluation scripts strip a leading `module.` prefix when they load checkpoints.
- They load the state dict with `strict=False` so compatible-but-not-identical checkpoints can still be evaluated.
