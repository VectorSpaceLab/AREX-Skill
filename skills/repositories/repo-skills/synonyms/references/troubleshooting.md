# Troubleshooting Synonyms

## Purpose

Use this when Synonyms import, model loading, lookup, similarity, segmentation, or vector workflows fail or produce confusing output.

## Import fails: `SYNONYMS_DL_LICENSE is not in Environment variables`

**Symptom**

```text
SYNONYMS_DL_LICENSE is not in Environment variables
```

**Likely cause**

The default packaged `words.vector.gz` model is missing and Synonyms cannot download the licensed model because no license id is set.

**Recover**

Choose one:

```bash
# Licensed download path.
export SYNONYMS_DL_LICENSE="<license-id>"
python -c "import synonyms; print(synonyms.describe())"

# Existing model path path.
export SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN="/path/to/words.vector.gz"
python -c "import synonyms; print(synonyms.describe())"

# API mechanics only; not semantic quality.
python scripts/synonyms_smoke_probe.py --use-tiny-fixture
```

Set the environment variable before the Python process imports `synonyms`.

## Model env var appears ignored

**Symptom**

You set a word2vec path but Synonyms still tries to use/download the default model.

**Likely cause**

The source checks `SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN`. Some README text shows `_SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN_` with surrounding underscores; that spelling is not the source-verified variable.

**Recover**

```bash
export SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN="/path/to/words.vector.gz"
python scripts/synonyms_smoke_probe.py --model-path "$SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN"
```

## `Model file [...] does not exist` or model-format errors

**Likely causes**

- The env var points to a missing file.
- The file is not binary word2vec format readable by Synonyms.
- A tiny/custom model has fewer tokens than the requested `nearby(..., size)`.
- A custom model dimensionality differs from the 100-dimensional assumptions in OOV fallback code.

**Recover**

1. Check the path exists and is readable.
2. Use a binary word2vec `.gz` model when passing `SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN`.
3. For custom diagnostic fixtures, prefer 100 dimensions and request `size <= vocab_size`.
4. Rerun:

```bash
python scripts/synonyms_smoke_probe.py --model-path /path/to/words.vector.gz --topk 5
```

## OOV words return empty or raise `KeyError`

**Symptoms**

- `synonyms.nearby("word")` returns `([], [])`.
- `synonyms.v("word")` raises `KeyError`.

**Cause**

The word is not in the loaded word2vec vocabulary.

**Recover**

- Treat empty `nearby` results as vocabulary coverage failure, not proof that the word has no synonyms.
- Catch `KeyError` around `v`.
- Use a fuller model or choose a word known to exist.
- The public FAQ says adding words to the Synonyms vocabulary is not supported as a normal package workflow.

## Sentence similarity looks unstable or unexpectedly nonzero

**Likely causes**

- `compare` combines vector similarity with a Levenshtein-style character signal.
- With `ignore=False`, OOV terms can receive deterministic random fallback vectors.
- `seg=False` expects whitespace-tokenized inputs; raw Chinese strings with `seg=False` are not the normal path.
- A tiny fixture validates mechanics only and cannot produce meaningful semantic scores.

**Recover**

```python
score = synonyms.compare("旗帜引领方向", "旗帜指引道路", seg=True, ignore=True)
```

Use a real full/equivalent model and a fixed evaluation fixture before judging score quality.

## Import output is noisy

**Symptom**

`import synonyms` prints project notices, jieba dictionary loading logs, model loading messages, and sometimes a `smart_open` fallback message.

**Cause**

This is import-time behavior in the package. It is normal but inconvenient for services/notebooks.

**Recover**

- Import once during application startup after env vars are configured.
- In diagnostic scripts, capture stdout/stderr around import.
- Set `SYNONYMS_DEBUG=TRUE` only when you intentionally want extra package debug messages.

## `smart_open library not found; falling back to local-filesystem-only`

**Meaning**

`synonyms.utils` did not find optional `smart_open` and installed a local-file fallback. This is acceptable for local `.gz` model files.

**Recover**

If your workflow truly needs remote smart-open URI support, install and verify `smart_open` explicitly in your environment. Otherwise ignore the message.

## Custom segmentation dictionary does not apply

**Likely causes**

- `SYNONYMS_WORDSEG_DICT` was set after import.
- The variable points to a missing file.

**Recover**

```bash
export SYNONYMS_WORDSEG_DICT="/path/to/jieba_dict.txt"
python -c "import synonyms; print(synonyms.seg('中文近义词工具包'))"
```

Set the variable before the Python process imports `synonyms`.

## Avoid unsafe source-maintainer scripts

Do not use repository release/upload scripts for runtime package troubleshooting. The runtime-safe replacement is:

```bash
python scripts/synonyms_smoke_probe.py --use-tiny-fixture
```

Use real model checks only when you have a license or existing compatible model path.
