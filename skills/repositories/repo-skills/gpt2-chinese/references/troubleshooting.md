# Troubleshooting

## Purpose

Read this when the repo imports, CLIs, tokenizer paths, or generation loops behave unexpectedly.

## Missing or outdated dependencies

### Symptom

- `ModuleNotFoundError` for `transformers`, `torch`, `thulac`, `sentencepiece`, or `tensorboard`.
- `train.py --help` prints a warning about `scikit-learn`.
- `cache/make_vocab.py` fails immediately on `keras.preprocessing.text.Tokenizer`.

### Likely cause

The repo is an old, pre-packaged codebase and its `requirements.txt` does not fully describe the runtime stack used by the current scripts.

### Next step

- Install a compatible PyTorch build first.
- Install the repo dependencies.
- Add `tensorboard`, `sentencepiece`, and `scikit-learn` when needed.
- Prefer the bundled vocabulary helper instead of the legacy keras-based `cache/make_vocab.py`.

## Training problems

### Symptom

- `assert log_step % gradient_accumulation == 0` fails.
- Training crashes when `--raw` is used.
- Training is very slow on CPU.
- `fp16` raises an Apex import error.

### Likely cause

- `log_step` and gradient accumulation are inconsistent.
- The corpus is not a JSON list of strings.
- CPU-only execution is expected to be slow for a GPT-2 training loop.
- Apex is not installed or the hardware is not CUDA-compatible.

### Next step

- Make `log_step` a multiple of `gradient_accumulation`.
- Check that the corpus is a JSON list of article strings.
- Leave `--fp16` off unless you have a matching CUDA/Apex stack.

## Evaluation problems

### Symptom

- `eval.py` prints a perplexity but no file appears.
- The script creates `output_dir` but `result.txt` is missing.

### Likely cause

The current evaluation code only writes the file when the output directory already exists.

### Next step

- Create the output directory before running the script, or patch the write branch if you need a persistent score file.

## Generation problems

### Symptom

- `generate.py` or `generate_texts.py` appears to hang.
- Output repeats the same sample more than once.
- Generated text ignores the `--no_wordpiece` flag.

### Likely cause

- `--nsamples` is not divisible by `--batch_size` in `generate.py`.
- The generation loop is not truly vectorized; larger batch sizes can duplicate output.
- The current code parses `--no_wordpiece` but does not actually branch on it.

### Next step

- Keep `--batch_size 1` unless you intentionally want the current repeated-sample behavior.
- Make `--nsamples` divisible by `--batch_size`.
- Use `--prefix "[CLS]..."` for the usual checkpoints.

## Tokenizer problems

### Symptom

- Importing the word-level tokenizer fails with `FileNotFoundError` for `tokenizations/thulac_dict/seg`.
- BPE mode fails with a missing `sentencepiece` error.
- A vocabulary file does not match the model config.

### Likely cause

- The word-level tokenizer uses a relative user dictionary path at import time.
- The BPE tokenizer requires the extra dependency and the encoder files.
- The tokenizer vocab and `model_config*.json` `vocab_size` are out of sync.

### Next step

- Run the checkout from its repository root or use the bundled helper that accepts `--repo-root`.
- Install `sentencepiece` for BPE mode.
- Rebuild or reselect the vocabulary so it matches the config.

## Checkpoint and path problems

### Symptom

- `model_path` or `pretrained_model` cannot be found.
- A `save_path`, `output_dir`, or `tokenized_data_path` directory is missing.

### Likely cause

The CLI expects a directory, not a file, for saved checkpoints and output roots.

### Next step

- Point `--model_path` and `--pretrained_model` at a directory produced by `save_pretrained`.
- Create output directories before running scripts that do not create them in every branch.
