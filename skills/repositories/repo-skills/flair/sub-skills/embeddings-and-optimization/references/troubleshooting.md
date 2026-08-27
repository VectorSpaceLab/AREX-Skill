# Embedding Troubleshooting

## Baseline triage

When an embedding workflow fails, first identify which class owns the failing path:

1. Is it token-level (`TokenEmbeddings`) or document-level (`DocumentEmbeddings`)?
2. Does the constructor use a named pretrained resource that may download, or only in-memory/local data?
3. Was `FLAIR_DEVICE` and `FLAIR_CACHE_ROOT` set before importing `flair`?
4. Are stale tensors still attached to the `Sentence` or `Token` objects?
5. Is the issue in ordinary PyTorch, optional ONNX/TorchScript/provider runtime, or a layout/OCR/image metadata path?

Use the no-download smoke to separate package/API problems from remote model problems:

```bash
python scripts/embedding_smoke.py --json
```

## Downloads and cache surprises

Symptoms:

- Constructor hangs or fails when creating `TransformerWordEmbeddings`, `TransformerDocumentEmbeddings`, `WordEmbeddings("glove")`, `BytePairEmbeddings("en")`, or `FlairEmbeddings("news-forward")`.
- Resource appears in a user cache that the caller did not expect.
- Offline job fails after working on another machine.

Actions:

- Set `FLAIR_CACHE_ROOT` before importing `flair`, then restart the Python process.
- Treat public identifiers as download-capable unless the file is already cached.
- For transformers, pre-download or point Hugging Face to an approved cache using normal `transformers` mechanisms. Keep those paths out of generated skill files and public recipes.
- For `WordEmbeddings`, verify optional `gensim` support and whether the requested identifier is public or a local file.
- For `BytePairEmbeddings`, verify `bpemb` availability and either cached BPEmb resources or explicit local `model_file_path` / `embedding_file_path`.
- For `FlairEmbeddings`, verify that the named LM resource or local `best-lm.pt` path exists.
- If network access is not allowed, switch to a no-download baseline such as `OneHotEmbeddings`, `CharacterEmbeddings`, or caller-provided local vectors.

## Device placement surprises

Symptoms:

- Tensors appear on CUDA unexpectedly.
- Static vectors are on CPU while model training expects CUDA.
- Changing `FLAIR_DEVICE` inside a process has no effect.

Actions:

- Set `FLAIR_DEVICE=cpu` before importing `flair` for CPU baseline work.
- Remember Flair selects `cuda:0` at import time when CUDA is available and `FLAIR_DEVICE` is not `cpu`.
- Start a new process after changing `FLAIR_DEVICE`.
- For `WordEmbeddings(fine_tune=True)` on CUDA, set `force_cpu=False`; Flair raises an error if trainable word embeddings are forced to CPU while training on GPU.
- For frozen `WordEmbeddings` or `BytePairEmbeddings`, `force_cpu=True` is a memory-saving default. It is not a proof that the whole pipeline is CPU-only.
- When debugging tensors, print both `str(flair.device)` and representative `token.get_embedding(names).device` or `sentence.get_embedding(names).device`.

## Stale or missing embeddings

Symptoms:

- `get_embedding()` length is larger than expected.
- A second embedding call appears to reuse old vectors.
- Vector checks pass for the wrong embedding family.
- Memory grows during prediction loops.

Actions:

- Use `embedding.get_names()` and pass names explicitly to `Token.get_embedding(names)` or `Sentence.get_embedding(names)`.
- Call `sentence.clear_embeddings()` between experiments, between PyTorch and optimized comparisons, and after prediction when tensors are not needed.
- For selective cleanup, pass names: `sentence.clear_embeddings(embedding.get_names())`.
- Avoid reusing the same `Sentence` object across incompatible embedding families unless cleanup is explicit.
- For model prediction, keep `embedding_storage_mode="none"` unless retaining embeddings is required.
- If embeddings must be retained for downstream logic, store only the needed CPU tensors and clear the Flair objects afterward.

## Shape mismatches

Symptoms:

- A downstream model reports decoder input dimension mismatches.
- Token vector lengths differ from the expected `embedding.embedding_length`.
- A stacked embedding doubles or widens unexpectedly.

Actions:

- Check `embedding.embedding_length` immediately after construction.
- Check exact names with `embedding.get_names()`.
- For `StackedEmbeddings`, remember final width is the sum of component widths and component names may be prefixed.
- For transformer token embeddings, `subtoken_pooling="first_last"` doubles token width.
- For transformer layers, `layer_mean=True` keeps one hidden-size width; `layer_mean=False` concatenates selected layers.
- For `BytePairEmbeddings`, width is `2 * dim`.
- For `DocumentRNNEmbeddings`, Flair reports `hidden_size` when unidirectional and `hidden_size * 4` when bidirectional.
- For `DocumentCNNEmbeddings`, width is the sum of kernel counts.
- Verify token-level vectors with every `Token.get_embedding(names)` and document-level vectors with `Sentence.get_embedding(names)`.

## Static embedding resource issues

### `WordEmbeddings`

Common causes:

- Unknown identifier or misspelled local path.
- Missing `gensim` support for loading word vectors.
- Header mismatch for word2vec text files.
- Attempting CUDA fine-tuning with `force_cpu=True`.

Fixes:

- Use known public ids such as `glove`, `en-glove`, `turian`, `extvec`, `crawl`, `news`, or language codes only when downloads/caches are approved.
- For custom vectors, convert to gensim or word2vec format and set `no_header=True` only when the first line does not contain vocab size and vector width.
- If vectors are already loaded in memory, pass both `vocab` and `embedding_length` with `embeddings=None`.

### `BytePairEmbeddings`

Common causes:

- Missing `bpemb` package.
- Cache/download unavailable.
- `language` omitted without `model_file_path`.
- Only a SentencePiece model was provided without `name`.

Fixes:

- Use `BytePairEmbeddings(language="en", dim=50, syllables=100000)` only when BPEmb resources may be downloaded or are cached.
- For fully local use, provide `model_file_path` and `embedding_file_path` when possible.
- If only `model_file_path` is supplied, also provide `name` and expect zero-initialized vectors unless a matching embedding file is supplied.

## Long sentences and context windows

Symptoms:

- Transformer tokenizer length errors or unexpected truncation.
- Output changes when sentences are embedded in a list rather than one at a time.
- Exported or traced models fail on longer production inputs.

Actions:

- For token embeddings, consider `allow_long_sentences=True` and validate with representative long examples.
- For document embeddings over long input, prefer `cls_pooling="mean"` or `"max"` when striding; CLS pooling over chunks is usually not useful.
- Use `use_context=True` or an integer only when neighboring sentence context is intended. Context changes the input sequence and can improve FLERT-style models but costs memory/time.
- Preserve document boundaries if context should not cross documents; `respect_document_boundaries=True` is the safe default.
- For optimization/tracing, include long/context examples in `example_sentences` and inspect `prepare_tensors` keys.
- Use `force_max_length=True` only for provider/tracing requirements after measuring the memory and speed cost.

## OCR, layout, and image model gaps

Symptoms:

- LayoutLM-style transformer embeddings raise errors about missing bounding boxes or images.
- Context with layout models warns or behaves unexpectedly.
- OCR dataset or image metadata examples work in tests but not in a service.

Actions:

- Treat OCR/layout/image transformer paths as optional/unverified unless the current environment has the model, image libraries, any feature-extractor dependencies, and representative metadata.
- Token-level layout models may require each token to carry `bbox` metadata.
- LayoutLMv2/v3-style paths may require sentence-level `image` metadata as well as token boxes.
- Do not assume Flair performs OCR for you. `needs_manual_ocr` and tokenizer/feature-extractor behavior are model-specific.
- Do not enable context windows for layout/OCR models unless the source data can supply consistent boxes/images for context tokens.
- If the task is ordinary text NLP, switch to a text-only transformer model.

## Language-model training and reuse failures

Symptoms:

- `TextCorpus` cannot find train/valid/test files.
- Fine-tuned LM fails to load as `FlairEmbeddings`.
- Forward/backward behavior appears reversed.
- LM training is too slow or memory-heavy.

Actions:

- Confirm layout: `corpus/train/`, `corpus/valid.txt`, and `corpus/test.txt`.
- Use `TextCorpus(path, dictionary, forward=is_forward_lm, character_level=True)` with the intended direction.
- Reuse the same dictionary and `is_forward_lm` when fine-tuning an existing LM.
- For named LM fine-tuning, load with `FlairEmbeddings("news-forward", has_decoder=True).lm` so the decoder is present.
- Start with small `hidden_size`, `nlayers`, `sequence_length`, `mini_batch_size`, and `max_epochs` for smoke checks. Do not extrapolate speed/quality claims from tiny runs.
- Use `checkpoint=True` only when resume artifacts are needed and disk space is available.
- Treat `use_amp=True` as backend-specific and unverified until the target device supports it.

## ONNX, TorchScript, and provider failures

Symptoms:

- `onnxruntime` import fails.
- Requested provider is missing.
- ONNX session cannot find the model file.
- TorchScript wrapper argument mismatch.
- Optimized output differs from PyTorch.

Actions:

- Read [Transformer optimization](transformer-optimization.md) and validate PyTorch baseline first.
- Check `onnxruntime.get_available_providers()` before requesting CUDA or other providers.
- Install operation-specific dependencies only when the caller wants this optional path: `onnxruntime` for CPU ONNX, `onnxruntime-gpu` plus compatible CUDA/cuDNN for CUDA provider, `onnx` and often `coloredlogs` for optimization, and `onnx` for quantization.
- Keep ONNX external data files together with the `.onnx` file.
- For TorchScript, print `sorted(embedding.prepare_tensors(examples).keys())` and make the wrapper signature match exactly.
- Compare token or document tensors against the PyTorch baseline after export, optimization, quantization, provider changes, and version changes.
- If comparison fails or latency regresses, keep the PyTorch model and report the optimization as unverified.

## When to ask for clarification

Ask the caller before proceeding when:

- The task would require downloading large pretrained resources and no download/cache policy is known.
- The requested runtime depends on CUDA, ONNX providers, OCR/image metadata, or proprietary compilers that are not verified.
- A local custom embedding file path, LM path, or corpus layout is missing.
- The caller wants to retain embeddings in memory but the dataset size or device memory budget is unknown.
