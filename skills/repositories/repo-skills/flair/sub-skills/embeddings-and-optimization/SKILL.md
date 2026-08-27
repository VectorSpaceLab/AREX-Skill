---
name: embeddings-and-optimization
description: "Routes Flair embedding-family selection, vector shape checks,
  language-model embedding reuse, storage/device behavior, and optional
  transformer optimization."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Flair Embeddings and Optimization

Use this sub-skill when the task involves embedding choices, vector extraction, vector-shape debugging, embedding storage, language-model embedding reuse, or optional acceleration for the public, pip-installed `flair` package. The verified baseline is CPU PyTorch execution. CUDA, ONNX providers, TorchScript speedups, model downloads, SciSpaCy, `pyab3p`, OCR/image pipelines, and provider runtimes are optional unless the current environment proves them.

## Route here for

- Choosing between `TokenEmbeddings` and `DocumentEmbeddings` for taggers, classifiers, relation models, entity-linking indices, sentence similarity, or standalone vector export.
- Configuring `TransformerEmbeddings`, `TransformerWordEmbeddings`, `TransformerDocumentEmbeddings`, `WordEmbeddings`, `FlairEmbeddings`, `PooledFlairEmbeddings`, `StackedEmbeddings`, `OneHotEmbeddings`, or `BytePairEmbeddings`.
- Building document vectors with `DocumentPoolEmbeddings`, `DocumentRNNEmbeddings`, `DocumentCNNEmbeddings`, or LM-backed document embeddings.
- Planning custom `LanguageModel` training/fine-tuning and reusing a saved LM with `FlairEmbeddings`.
- Debugging vector widths, stale embeddings, cache/download paths, device placement, storage modes, long sentences, context windows, OCR/layout metadata, ONNX, TorchScript, or execution-provider problems.

Use sibling training/dataset guidance for corpus readers, label dictionaries, `ModelTrainer.train`, classifier construction, TARS, multitask, checkpoints, or multi-GPU launches. Use sibling tagging/annotation guidance for prediction labels, tokenization, sentence splitting, serialization, visualization, and regex tagging. Use biomedical guidance for HunFlair/HunFlair2 or biomedical entity linking.

## Start safely

1. Set `FLAIR_DEVICE=cpu` before importing `flair` when CPU determinism is required.
2. Set `FLAIR_CACHE_ROOT` before importing `flair` when downloads are allowed and should be isolated to a caller-chosen cache.
3. Avoid constructing named pretrained resources unless downloads are acceptable or the assets are already cached. `Transformer*`, `WordEmbeddings("glove")`, `BytePairEmbeddings("en")`, and `FlairEmbeddings("news-forward")` may resolve remote resources.
4. Prefer `sentence.clear_embeddings()` after standalone vector extraction or prediction unless the caller explicitly needs stored tensors later.
5. Treat `embeddings_storage_mode="none"` as the conservative default for transformer fine-tuning or memory-constrained prediction.

## Read these references

- [Embedding recipes](references/embedding-recipes.md): concrete API recipes, family-selection rules, shape/device checks, storage modes, and language-model reuse.
- [Transformer optimization](references/transformer-optimization.md): optional ONNX/TorchScript/provider paths, dependencies, export checks, and validation comparisons.
- [Troubleshooting](references/troubleshooting.md): cache/download, stale embeddings, static resources, long sentence/context, OCR/image metadata, LM training, and provider-runtime failures.
- [Embedding smoke script](scripts/embedding_smoke.py): safe no-download CPU smoke checks for token/document embeddings.

## Quick decision map

| User need | Start with | Notes |
| --- | --- | --- |
| Token-level tagging or token vectors | `TransformerWordEmbeddings` or `TransformerEmbeddings(is_token_embedding=True)` | Use `layers="-1"` for fine-tuning; more layers increase width when concatenated. |
| Document/sentence classification vectors | `TransformerDocumentEmbeddings` or `DocumentPoolEmbeddings` | Transformer documents are direct; pool/RNN/CNN build on token embeddings. |
| No-download smoke or unit fixtures | `OneHotEmbeddings` plus `DocumentPoolEmbeddings` | CPU-safe and in-memory; vectors are random until trained. |
| Frozen classic stack | `StackedEmbeddings([WordEmbeddings(...), FlairEmbeddings(...), ...])` | Good for classic Flair workflows; named resources may download. |
| Small subword static baseline | `BytePairEmbeddings(language="en")` | Requires BPEmb resources from cache/download or local files. |
| Domain-specific contextual string embeddings | Train/reuse `LanguageModel` and pass `best-lm.pt` to `FlairEmbeddings` | Preserve LM direction and dictionary when fine-tuning or reusing. |
| Production transformer acceleration | ONNX or TorchScript after baseline comparison | Optional/unverified until dependencies, providers, and tensor comparisons pass. |

## Smoke check

From this sub-skill directory, run:

```bash
python scripts/embedding_smoke.py --json
```

The default smoke uses in-memory dictionaries and tiny trainable embeddings. It imports `flair`, forces the CPU baseline unless the caller already set another policy, checks token/document vector widths, and does not download models. Optional transformer checks require explicit flags and still do not prove CUDA, ONNX, TorchScript, or provider acceleration.
