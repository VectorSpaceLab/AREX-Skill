# Troubleshooting

## Package or command is missing

Symptoms:

- `ModuleNotFoundError: No module named 'bert_pytorch'`
- `bert: command not found`
- `bert-vocab: command not found`

Checks:

```bash
python scripts/check_install.py
python -m pip show bert_pytorch
```

Fixes:

- Install `bert-pytorch` into the Python environment you are actually using.
- Make sure the environment's `bin/` directory is on `PATH` before calling the console scripts.
- Re-run `python scripts/check_install.py` after installation to verify the package and commands.

## Corpus format is wrong

Symptoms:

- Dataset construction fails while reading lines.
- Vocab counts look too small or too large.
- Training examples do not look like sentence pairs.

Likely cause:

- The corpus is not one tab-separated sentence pair per line.
- Tokenization was skipped or mixed with raw text in a way the package does not expect.
- A line contains extra tabs or is blank.

Fixes:

- Rebuild the corpus so each line has exactly two fields separated by one tab.
- Tokenize before calling `bert-vocab`; the package only consumes whitespace-separated tokens.
- Use `python scripts/make_tiny_corpus.py --output /tmp/bert-pytorch-corpus.txt` as a known-good fixture.

## Streaming dataset mode is brittle

Symptoms:

- `BERTDataset(..., on_memory=False)` behaves strangely.
- The corpus length seems unknown or iteration does not stop where expected.

Likely cause:

- `corpus_lines` was omitted when streaming.

Fixes:

- Prefer `on_memory=True` for small or smoke-sized corpora.
- If you need streaming, pass an explicit `corpus_lines` value.

## Boolean CLI flags do not disable the way you expect

Symptoms:

- `--with_cuda False` still behaves like `True`.
- `--on_memory False` does not switch the loader off memory.

Likely cause:

- The CLI uses `type=bool`, so non-empty strings are truthy.

Fixes:

- Use `sub-skills/training/scripts/train_smoke.py` for explicit CPU or CUDA selection.
- Use the Python API when you need to pass `with_cuda=False` or `on_memory=False` directly.

## Hidden size and attention heads conflict

Symptoms:

- Model construction fails with an assertion about `d_model` and `h`.

Likely cause:

- `hidden` is not divisible by `attn_heads`.

Fixes:

- Choose a hidden size that divides evenly by the number of attention heads.
- For smoke runs, keep the values small and compatible, such as `hidden=32` and `attn_heads=4`.

## GPU or memory problems

Symptoms:

- CUDA is available but training is too slow or runs out of memory.
- The model unexpectedly lands on CPU.
- Multi-GPU training does not use all visible devices.

Fixes:

- Lower `batch_size`, `seq_len`, `hidden`, or `layers`.
- Use `sub-skills/training/scripts/train_smoke.py --device cpu` for a deterministic CPU smoke.
- Pass explicit CUDA device IDs only when you actually need `DataParallel`.

## Checkpoint path confusion

Symptoms:

- The saved model file is not named exactly like the `-o` argument.
- The output directory is missing.

Likely cause:

- `BERTTrainer.save()` appends `.ep{epoch}` to the file prefix and expects the parent directory to exist.

Fixes:

- Treat `-o` as a prefix, not the final checkpoint filename.
- Create the parent directory before saving.

## Pickle trust boundary

Symptoms:

- Loading a saved vocabulary fails or looks suspicious.

Likely cause:

- The vocabulary file is a Python pickle created by `WordVocab.save_vocab()`.

Fixes:

- Only load vocab files you trust.
- Regenerate the vocab with `bert-vocab` or the bundled smoke helper if the file is stale or corrupted.
