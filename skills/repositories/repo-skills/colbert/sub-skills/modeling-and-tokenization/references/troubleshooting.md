# Modeling and Tokenization Troubleshooting

## Import or Install Failures

Symptoms:

- `ModuleNotFoundError: No module named 'colbert'`.
- Importing modeling modules fails before any checkpoint is loaded.
- Old torch stacks fail around `setuptools`, `pkg_resources`, compiled extensions, or optional package imports.

Fixes:

- Confirm the installed distribution is `colbert-ai` and the import package is `colbert`.
- Start with lightweight imports: `import colbert`, `from colbert.infra import ColBERTConfig`, then `from colbert.modeling.checkpoint import Checkpoint`.
- If modeling import triggers PyTorch extension compilation, verify PyTorch, compiler, and Python package compatibility before debugging ColBERT APIs.
- For CPU-only environments, limit first checks to config/tokenizer inspection; training and practical indexing usually need CUDA/GPU.

## Checkpoint Config Is Missing

Symptoms:

- `ColBERTConfig.load_from_checkpoint(path)` returns `None`.
- `Checkpoint(path)` fails while merging config or loading weights.
- A directory has model files but no `artifact.metadata`.

Likely causes:

- The directory is a generic Hugging Face backbone, not a saved ColBERT checkpoint.
- ColBERT metadata was not copied with the model/tokenizer files.
- A legacy `.dnn` file lacks expected saved arguments.

Fixes:

- Run `scripts/inspect_checkpoint_config.py --checkpoint <local-path>` first.
- Use a ColBERT checkpoint directory saved with `artifact.metadata` when possible.
- For intentional generic-backbone work, pass an explicit `ColBERTConfig(checkpoint=<name-or-path>, query_maxlen=..., doc_maxlen=..., dim=...)` and verify model compatibility.
- Do not assume a generic Hugging Face model is a trained ColBERT retrieval checkpoint.

## Hugging Face Network or Cache Failures

Symptoms:

- A script hangs or fails on `hf_hub_download`, `from_pretrained`, or `AutoTokenizer.from_pretrained`.
- Authentication, offline, SSL, DNS, cache, or repository-not-found errors appear after passing a model name.

Reason: model names such as `colbert-ir/colbertv2.0` or `bert-base-uncased` can require Hugging Face Hub or local cache access.

Fixes:

- Prefer local checkpoint paths for deterministic automation.
- Use `--allow-remote` in bundled scripts only when remote/cache access is intentional.
- If remote access is blocked, download/copy the checkpoint separately and rerun against the local directory.
- Keep runtime skill instructions generic; do not bake local cache paths into scripts or references.

## Marker Tokens Are Unexpected

Symptoms:

- `ids[:, 1]` is not the query/document marker ID.
- Decoded text shows marker-like strings in odd places.
- A user pre-inserted `[Q]` or `[D]` into raw input text.

Expected behavior:

- Query marker ID appears at column `1`.
- Document marker ID appears at column `1`.
- `query_token_id='[unused0]'` and `doc_token_id='[unused1]'` are converted through the underlying tokenizer vocabulary.

Fixes:

- Use `scripts/tokenization_smoke.py --checkpoint <local-checkpoint>`.
- Confirm `config.query_token_id` and `config.doc_token_id` exist in the tokenizer vocabulary.
- Do not pre-insert marker IDs or marker strings into raw text.
- If using a non-BERT tokenizer, verify that the first special-token convention still makes column `1` a valid marker position.

## Query Max Length, Masks, and Truncation

Symptoms:

- Query IDs/masks are shorter or longer than expected.
- Decoded queries contain many `[MASK]` tokens.
- `full_length_search=True` fails for a batch.
- Changing `query_maxlen` changes ranking cost or shape assumptions.

Expected behavior:

- Normal query width is `config.query_maxlen`.
- Raw tokenizer truncates to `query_maxlen - 1`; ColBERT inserts the marker to reach `query_maxlen`.
- Pad IDs are replaced by `[MASK]` IDs.
- Attention masks do not attend to those mask positions unless `attend_to_mask_tokens=True`.
- `full_length_search=True` is only valid for one query in a list.

Fixes:

- Inspect `query_maxlen` with `scripts/inspect_checkpoint_config.py`.
- Use `scripts/tokenization_smoke.py --verbose` to decode query IDs.
- Do not compare decoded `[MASK]` padding to document padding behavior; they are intentionally different.

## Document Max Length and Punctuation Masking

Symptoms:

- Document tensor width is not exactly `doc_maxlen`.
- Passage tails disappear after lowering `doc_maxlen`.
- Punctuation tokens appear in decoded IDs but not in document embeddings.

Expected behavior:

- `DocTokenizer` uses longest padding within the batch, capped by `doc_maxlen`.
- It tokenizes with `max_length=doc_maxlen - 1`, then inserts the `[D]` marker.
- `mask_punctuation=True` removes/zeros punctuation document embeddings in `ColBERT.doc()`, not during raw tokenization.

Fixes:

- Compare `d_ids.shape[1] <= config.doc_maxlen`, not equality for every short batch.
- Increase `doc_maxlen` if important passage tail tokens are truncated.
- Set `mask_punctuation=False` only when you intentionally want punctuation document embeddings retained and understand index/search compatibility implications.

## Dimension or Checkpoint Mismatch

Symptoms:

- Model loading fails with projection weight shape mismatches.
- Encoded embeddings have a dimension different from downstream expectations.
- A user changes `dim` while reusing an incompatible checkpoint.

Fixes:

- Treat `dim` as checkpoint-weight-sensitive, not a harmless runtime knob.
- Inspect `dim` from metadata before model loading.
- Only change `dim` when initializing/training a compatible model or loading weights with matching projection shape.

## CPU/GPU Device Issues

Symptoms:

- Tensors unexpectedly live on CUDA.
- CPU-only consumers fail on CUDA tensors.
- CUDA is unavailable even though config says GPU-oriented flows are expected.

Expected behavior:

- Tokenizer tensors are moved to `colbert.parameters.DEVICE`.
- `BaseColBERT` moves the model to that same device.
- `Checkpoint.queryFromText(..., to_cpu=True)` and `Checkpoint.docFromText(..., to_cpu=True)` move encoded outputs back to CPU.
- Practical indexing/training usually needs CUDA/GPU, even if import and config inspection work on CPU.

Fixes:

- Use `to_cpu=True` for inspection and downstream CPU consumers.
- Check `torch.cuda.is_available()` and CUDA visibility before launching Python.
- Route full indexing/search backend failures to indexing-and-search after tokenizer/model checks pass.

## API Misuse

Common mistakes:

- Passing a single string instead of a list/tuple to `QueryTokenizer.tensorize()` or `DocTokenizer.tensorize()`.
- Passing both marker-prepended input and using ColBERT tensorizers.
- Expecting `DocTokenizer.tensorize()` with `bsize` to return `(ids, mask)` instead of `(batches, reverse_indices)`.
- Expecting `docFromText(..., keep_dims='flatten')` to return a padded 3-D tensor.
- Running network-dependent tokenizer tests in offline mode.

Fixes:

- Wrap one example as `['text']`.
- Let ColBERT insert markers.
- Read `references/api-reference.md` before changing `bsize` or `keep_dims`.
- Run smoke scripts first with local checkpoints, then intentionally enable remote behavior only when needed.
