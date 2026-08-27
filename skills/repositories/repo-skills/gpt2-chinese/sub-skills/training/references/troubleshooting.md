# Training Troubleshooting

## Purpose

Read this when `train.py`, `train_single.py`, or `eval.py` does not behave as expected.

## Workflow-specific failures

### `log_step` assertion fails

- **Symptom:** `assert log_step % gradient_accumulation == 0`.
- **Cause:** the logging interval does not line up with the accumulation schedule.
- **Fix:** choose a `log_step` that is divisible by `gradient_accumulation`.

### Raw preprocessing fails

- **Symptom:** `--raw` crashes while building tokenized pieces.
- **Cause:** the corpus is not a JSON list of strings or the path is wrong.
- **Fix:** make sure `train.json` / `eval.json` contain a top-level list of article strings.

### Training is much slower than expected

- **Symptom:** the loop runs but progress is extremely slow.
- **Cause:** CPU-only execution or an unexpectedly large config.
- **Fix:** use the tiny test config for smoke checks; use CUDA when you actually need throughput.

### Mixed precision fails

- **Symptom:** `ImportError` for Apex or `fp16` instability.
- **Cause:** Apex is missing or the GPU stack is not compatible.
- **Fix:** leave `--fp16` off unless you explicitly prepared an Apex/CUDA environment.

### Checkpoint continuation does not load

- **Symptom:** `--pretrained_model` or `eval.py --pretrained_model` cannot find a model.
- **Cause:** the path is not a directory created by `save_pretrained`.
- **Fix:** point the flag at the checkpoint directory, not a file inside it.

### Evaluation score file is missing

- **Symptom:** perplexity is printed but `result.txt` is not created.
- **Cause:** the current `eval.py` write branch only fires when the output directory already exists.
- **Fix:** create the directory first or patch the write branch if you need the file.

### TensorBoard import errors

- **Symptom:** `SummaryWriter` import fails.
- **Cause:** `tensorboard` is missing even though PyTorch is present.
- **Fix:** install `tensorboard` in the environment.

### Config, vocab, and checkpoint mismatch

- **Symptom:** shape errors, broken loss, or nonsense continuation after loading.
- **Cause:** the config `vocab_size`, tokenizer file, and checkpoint were built against different token sets.
- **Fix:** keep the same config and vocabulary bundle together, or rebuild the checkpoint with a matching pair.
