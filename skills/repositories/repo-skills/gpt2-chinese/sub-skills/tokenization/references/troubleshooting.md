# Tokenization Troubleshooting

## Purpose

Read this when the tokenizer import, vocabulary path, or segmentation mode fails.

## Workflow-specific failures

### Word-level tokenizer cannot import its dictionary

- **Symptom:** `FileNotFoundError` for `tokenizations/thulac_dict/seg`.
- **Cause:** the tokenizer loads a relative user dictionary at import time, so the working directory is wrong.
- **Fix:** run from the repository root or use a helper that points at the checkout root before importing the tokenizer.

### BPE mode fails immediately

- **Symptom:** `ModuleNotFoundError` for `sentencepiece` or missing `encoder.json` / `vocab.bpe`.
- **Cause:** the BPE path needs both the dependency and the tokenizer files.
- **Fix:** install `sentencepiece` and verify both BPE files exist before trying the BPE path.

### Vocabulary building still tries to use keras

- **Symptom:** the legacy `cache/make_vocab.py` crashes on `keras.preprocessing.text.Tokenizer`.
- **Cause:** that script is an old source artifact and its dependency set is stale.
- **Fix:** use the bundled `scripts/build_vocab.py` helper instead of the legacy source script.

### Vocab and config do not match

- **Symptom:** strange load errors or nonsense outputs after changing tokenizer mode.
- **Cause:** the tokenizer vocabulary and model config `vocab_size` no longer agree.
- **Fix:** keep the same tokenizer bundle with the same config, or rebuild both together.

### Segmentation changes the model behavior unexpectedly

- **Symptom:** outputs differ sharply after switching `--segment` on or off.
- **Cause:** the corpus was trained with a different tokenization style.
- **Fix:** keep training and generation on the same tokenizer mode and vocabulary bundle.

### The helper output looks different from the legacy vocab builder

- **Symptom:** a fresh vocab built by the bundled helper does not match the old script byte-for-byte.
- **Cause:** the bundled helper is a safe replacement, not a perfect clone of the old keras pipeline.
- **Fix:** treat the helper as the preferred runtime path and only compare outputs at the token list level, not by file identity.
