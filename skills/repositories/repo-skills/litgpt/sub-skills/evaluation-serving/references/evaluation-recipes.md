# Evaluation Recipes

Use these recipes to plan LitGPT evaluation with LM Evaluation Harness without accidentally starting a large benchmark or relying on original repository files.

## Preflight Checklist

1. Check optional dependency availability:
   `python scripts/check_optional_eval_serve_deps.py --mode evaluate --checkpoint-dir CHECKPOINT_DIR --batch-size 1`.
2. Confirm checkpoint layout; if `lit_model.pth`, tokenizer files, or model config are unclear, route to `../../checkpoint-conversion/`.
3. Choose one or a small CSV of LM Harness tasks. For discovery, run `litgpt evaluate list` and filter the output.
4. Use `--limit` for smoke runs. Full tasks may download datasets and run for a long time.
5. Choose explicit output paths when another agent needs artifacts: `--out_dir eval-out --save_filepath eval-out/results.json`.
6. Decide whether conversion can reuse cached HFLM files or needs `--force_conversion true`.

## Minimal Smoke Evaluation

```bash
litgpt evaluate CHECKPOINT_DIR \
  --tasks hellaswag \
  --batch_size 1 \
  --limit 10 \
  --device cpu \
  --out_dir eval-out \
  --save_filepath eval-out/results.json
```

Use CPU only for tiny checkpoints or validation of command shape; real models are usually too slow on CPU.

## Full or Multi-Task Evaluation

```bash
litgpt evaluate CHECKPOINT_DIR \
  --tasks hellaswag,truthfulqa_mc2,mmlu \
  --batch_size auto:4 \
  --device cuda \
  --dtype float16 \
  --seed 1234 \
  --out_dir eval-out \
  --save_filepath eval-out/results.json
```

Notes:

- `--batch_size auto` or `auto:N` lets LM Harness infer a batch size; `auto:4` recomputes multiple times.
- A positive integer batch size is accepted. Non-positive integers and strings that do not start with `auto` are rejected.
- `--seed` feeds random, NumPy, and torch seed arguments in the evaluation call.
- `--num_fewshot` should match task expectations and evaluation protocol.

## Conversion Behavior

`litgpt evaluate` does an internal conversion for HFLM:

1. Selects or downloads/locates the checkpoint.
2. Creates `--out_dir` or defaults to `checkpoint_dir/evaluate`.
3. Copies config files to the evaluation output directory.
4. Converts the LitGPT checkpoint into a temporary `model.pth`.
5. Re-saves it as `pytorch_model.bin` so HFLM can load it.
6. Reuses existing converted files unless `--force_conversion true` is supplied.

Use `--force_conversion true` when:

- The LitGPT checkpoint changed after a prior evaluation.
- The converted `pytorch_model.bin` looks stale.
- A previous evaluation failed during or after conversion and left partial files.

## Task Listing and Result Files

Task listing:

```bash
litgpt evaluate list
litgpt evaluate list | grep mmlu
```

Result collection:

- Console output contains table-formatted metrics and group tables when present.
- The JSON result file contains the raw LM Harness result dictionary.
- Default result path is `out_dir/results.json`.
- Prefer an explicit `--save_filepath` for automation so downstream checks know the path.

## Diagnosing the Hard Case: `batch_size='zero'` plus Missing `lm_eval`

Recommended safe response:

1. Do not run a benchmark yet.
2. Run `python scripts/check_optional_eval_serve_deps.py --mode evaluate --batch-size zero --checkpoint-dir CHECKPOINT_DIR`.
3. Report both issues:
   - `lm_eval` is missing, so task listing/evaluation cannot import the harness.
   - `batch_size` must be a positive integer, `auto`, or `auto:N`; use `1` for the smallest deterministic fix.
4. Minimal corrected command after installing `lm_eval`:

```bash
litgpt evaluate CHECKPOINT_DIR \
  --tasks hellaswag \
  --batch_size 1 \
  --limit 10 \
  --out_dir eval-out \
  --save_filepath eval-out/results.json
```

## What Not To Do

- Do not use `litgpt evaluate` for arbitrary custom JSON scoring; LitGPT docs describe custom evaluation as a separate generate-and-score workflow, not a built-in command.
- Do not assume all task names are installed or cached; LM Harness may trigger dataset access.
- Do not hide large benchmark downloads behind a helper script.
- Do not pass secrets directly into reusable scripts or public skill content.
