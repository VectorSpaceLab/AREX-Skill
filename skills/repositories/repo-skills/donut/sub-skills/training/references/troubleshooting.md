# Troubleshooting

Start with the bundled helper scripts:

- `scripts/check_training_config.py` for config and local JSONL issues
- `scripts/evaluate_dataset.py --validate_only` for dataset-only validation

## CUDA / driver mismatch

**Symptom:** training exits before the first step, or `torch.cuda.is_available()` is false.

**Why it happens:** `train.py` hard-codes GPU, DDP, and 16-bit execution. There is no honest CPU substitute for the training workflow in this repository.

**Fix:** verify the CUDA runtime, NVIDIA driver, and PyTorch wheel stack together. Training needs a working CUDA backend.

## Missing runtime dependency

**Symptom:** `ModuleNotFoundError` for `datasets`, `pytorch_lightning`, `transformers`, `sconf`, `timm`, `sentencepiece`, `nltk`, or `zss`.

**Why it happens:** the repo depends on the installed `donut-python` runtime plus the training stack.

**Fix:** install the runtime dependencies in the inspection or working environment before attempting config checks or training.

## Malformed `metadata.jsonl`

**Symptom:** JSON decode errors, missing `file_name`, or missing `ground_truth` during dataset inspection.

**Why it happens:** each line in `metadata.jsonl` must be valid JSON, and `ground_truth` must be a JSON-encoded string.

**Fix:** repair the line format first. A valid row looks like `{"file_name": "train/0001.png", "ground_truth": "{...}"}`.

## Missing `gt_parse` or `gt_parses`

**Symptom:** `KeyError` or schema validation failures for a task dataset.

**Why it happens:** single-answer tasks need `gt_parse`; DocVQA-style tasks need `gt_parses`.

**Fix:**

- use `gt_parse` for CORD, RVL-CDIP, TrainTicket, and the text-reading task
- use `gt_parses` for DocVQA
- keep each nested value typed correctly (`dict` for `gt_parse`, `list[dict]` for `gt_parses`)

## Prompt-token mismatch

**Symptom:** validation loss looks normal but predictions are malformed, or evaluation uses the wrong prompt.

**Why it happens:** the task token, prompt end token, and dataset schema must align.

**Fix:**

- DocVQA uses `<s_answer>` as the prompt end token and expects the first question from `gt_parses`
- RVL-CDIP adds class special tokens automatically in the trainer
- non-DocVQA tasks default to the task token as both the task start token and the prompt end token
- if you override `task_start_tokens`, keep the list aligned with the dataset list

## Multi-dataset `max_epochs` constraint

**Symptom:** training aborts with the assertion `Set max_epochs only if the number of datasets is 1`.

**Why it happens:** the optimizer setup computes the number of iterations from a single dataset when `max_epochs > 0`.

**Fix:**

- use only one dataset when `max_epochs` is set
- or switch to `max_steps` for multi-dataset training

## Batch-size list mismatch

**Symptom:** one or more datasets appear to be ignored, or validation looks shorter than expected.

**Why it happens:** the source code zips datasets with `train_batch_sizes` and `val_batch_sizes`.

**Fix:** keep the dataset list and both batch-size lists the same length. The bundled config checker flags this early.

## Checkpoint path issues

**Symptom:** resume fails to find `artifacts.ckpt` or `pytorch_model.bin`.

**Why it happens:** the Donut checkpoint layout stores the model files alongside the trainer checkpoint in the run directory.

**Fix:** point `resume_from_checkpoint_path` at the run directory prefix that contains the saved checkpoint and model files, not at the top-level `result_path`.

## Lightning version quirks

**Symptom:** seeding or trainer behavior changes after an environment upgrade.

**Why it happens:** the source code branches on the major Lightning version and uses a different seeding helper in Lightning 2.x.

**Fix:** use the tested Lightning stack when possible and re-run the helper scripts after any version change.

## Metric interpretation confusion

**Symptom:** one run looks better than another, but the metric direction is unclear.

**Fix:** remember that `val_metric` and normalized edit distance are lower-is-better, while `ted_accuracy` and `f1_accuracy` are higher-is-better. Do not compare them without accounting for direction.
