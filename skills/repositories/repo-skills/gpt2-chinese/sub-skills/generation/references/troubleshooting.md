# Generation Troubleshooting

## Purpose

Read this when `generate.py` or `generate_texts.py` hangs, repeats output, or cannot load a checkpoint.

## Workflow-specific failures

### Generation hangs or never reaches the break condition

- **Symptom:** the CLI keeps looping after it has already emitted some samples.
- **Cause:** `generate.py` only exits when the emitted count exactly matches `nsamples`.
- **Fix:** keep `--nsamples` divisible by `--batch_size`.

### Repeated outputs appear inside one batch

- **Symptom:** the same text is printed more than once per loop.
- **Cause:** the current CLI does not vectorize decoding; the outer loop reuses one generated sample across the inner batch count.
- **Fix:** keep `--batch_size 1` unless you intentionally want the current repeated-sample behavior.

### Prompt text looks wrong

- **Symptom:** the output starts strangely or misses the desired style.
- **Cause:** the prompt was not prefixed the way the checkpoint expects.
- **Fix:** use a `[CLS]`-prefixed prompt for the usual pretrained checkpoints.

### `--no_wordpiece` seems to do nothing

- **Symptom:** the flag parses, but the output does not change.
- **Cause:** the current generation scripts accept the flag but do not branch on it.
- **Fix:** choose the tokenizer mode explicitly with `--segment` or the relevant vocab path.

### Checkpoint loading fails

- **Symptom:** `model_path` cannot be loaded with `from_pretrained`.
- **Cause:** the path is not a saved checkpoint directory or the config/vocab does not match.
- **Fix:** point the flag at the directory created by `save_pretrained` and keep the matching vocab bundle.

### Saved files do not appear

- **Symptom:** stdout shows text, but no `samples.txt` or article files appear.
- **Cause:** the save directory is wrong or `--save_samples` / `--save_path` was not enabled.
- **Fix:** create the save directory and pass the correct save flag.

### Fast pattern smoke fails

- **Symptom:** `--fast_pattern` or the helper smoke crashes on a cached-past call.
- **Cause:** the model or tokenizer is not loadable, or the checkpoint/config pair is inconsistent.
- **Fix:** first confirm the model loads and the tiny smoke config works; then retry `--fast_pattern`.
