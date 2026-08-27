# Model and Environment Reference

## Purpose

Read this before importing `synonyms`, setting up a model, or diagnosing first-use behavior. Synonyms loads its model at import time, so environment variables must be in place before the first `import synonyms` in a Python process.

## Package install surface

The repository builds the Python distribution `synonyms` with import name `synonyms`. The package metadata declares these runtime dependencies: `six`, `numpy`, `scipy`, `scikit-learn`, `jieba`, and `chatoperastore`.

Typical install:

```bash
pip install -U synonyms
```

A checkout/development install can use:

```bash
pip install -e /path/to/Synonyms
```

There are no package console entry points in the repository metadata. Use Python imports or the bundled diagnostic script in this skill.

## Import-time model behavior

`import synonyms` does more than register functions:

1. Prints package/project notices.
2. Configures jieba with packaged dictionaries.
3. Loads packaged stopwords.
4. Loads a word2vec model into a KDTree-backed `KeyedVectors` object.

If no model file is already available and no supported model path is supplied, the package attempts licensed model handling. Without `SYNONYMS_DL_LICENSE`, import fails with a message like:

```text
SYNONYMS_DL_LICENSE is not in Environment variables
```

Set model-related variables before Python starts or before the first `import synonyms`.

## Environment variables

| Variable | Source-verified behavior | Use when |
| --- | --- | --- |
| `SYNONYMS_DL_LICENSE` | License id used by `chatoperastore.download_licensedfile` when the default packaged `words.vector.gz` is missing. | You have a Chatopera license and want Synonyms to download the official model on first import. |
| `SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN` | Overrides the model file path and disables the download branch. The model must be a binary word2vec-format file readable by the package. | You already have a compatible model file or want an offline/private model path. |
| `SYNONYMS_WORDSEG_DICT` | If it points to an existing file, Synonyms uses it as the jieba word-segmentation dictionary. | You need a custom segmentation dictionary. |
| `SYNONYMS_DEBUG` | When set to `TRUE` case-insensitively, enables extra debug prints in Synonyms helpers. | You are debugging similarity/vector internals. |

Important naming caveat: the README table shows `_SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN_` with surrounding underscores, but source and live inspection confirmed the variable actually checked by the package is `SYNONYMS_WORD2VEC_BIN_MODEL_ZH_CN`.

## Word2vec model requirements

The package loader expects a word2vec-format model and calls `KeyedVectors.load_word2vec_format(..., binary=True)`. The official model is documented as `words.vector.gz` with a large Chinese vocabulary. Production similarity quality depends on that full/equivalent model.

For custom or diagnostic models:

- Prefer a 100-dimensional binary word2vec `.gz` model. Source OOV fallback vectors are hard-coded to length 100; non-100-dimensional custom models can expose shape-mismatch edge cases when OOV words are mixed into sentence vector workflows.
- Include every word that must be queried with `v(word)`; `v` raises `KeyError` for OOV terms.
- `nearby(word, size)` uses a KDTree query; do not request `size` larger than the custom fixture vocabulary when testing with a tiny model.

## Safe smoke checks

Use the bundled probe instead of repository-local demos:

```bash
# Mechanics-only check; generates a temporary tiny model.
python scripts/synonyms_smoke_probe.py --use-tiny-fixture --word 人脸

# Real/equivalent model check.
python scripts/synonyms_smoke_probe.py --model-path /path/to/words.vector.gz --word 飞机
```

The first command verifies package import, API signatures, segmentation, keyword extraction, nearby lookup, vector shape, and compare output. It does not verify real semantic quality.

## Optional `smart_open` note

`synonyms.utils` tries to import `smart_open`; if unavailable it prints a fallback message and uses local-file-only open logic. The package metadata does not install `smart_open`. This is acceptable for local/gzip model files, but remote smart-open URI behavior is not part of the selected runtime scope.
