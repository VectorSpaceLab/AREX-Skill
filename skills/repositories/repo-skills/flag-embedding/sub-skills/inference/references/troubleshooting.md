# Inference Troubleshooting

This reference covers workflow-specific inference issues. For package
installation, import failures before inference code runs, missing global
optional dependencies, or environment repair, route to the root skill
troubleshooting reference at `../../references/troubleshooting.md`.

## Auto Mapping Misses

Symptom:

```text
Model name '<name>' not found in the model mapping.
```

Likely causes:

- The checkpoint is local and its basename is not a built-in mapping key.
- The path ends with `checkpoint-N`; auto mapping uses the parent directory
  basename.
- The checkpoint is a custom fine-tuned model whose architecture is known but
  not registered in the mapping.
- A provider-qualified remote id is represented differently from the basename
  used by the auto loader.

Recovery:

1. Choose the correct `model_class` from `references/api-reference.md`.
2. For embedders, set `pooling_method`, `query_instruction_format`, and
   `trust_remote_code` explicitly.
3. For rerankers, set `query_max_length`, `max_length`, and any layerwise or
   lightweight options explicitly.
4. Smoke-check with `scripts/smoke_inference_api.py --model-name ... --model-class ... --devices cpu`.

Do not assume a model is incompatible just because auto mapping misses it.

## Remote-Code And Custom-Code Loading

Symptom:

- Loading fails with an unknown architecture, missing custom class, or
  transformer auto-model error.
- Layerwise or lightweight rerankers fail when custom modeling files are not
  available.

Recovery:

- Keep `trust_remote_code=False` for standard checkpoints.
- Set `trust_remote_code=True` only when the checkpoint requires custom model
  code and the code has been reviewed.
- For local layerwise or lightweight rerankers, ensure the checkpoint directory
  contains the custom configuration/model files required by that checkpoint.
- If the failure is an install/import issue, route to root troubleshooting.

## Cache, Network, And Offline Loads

Symptom:

- Loading a model id unexpectedly starts a download.
- Offline loading fails even though the checkpoint name looks correct.
- A cache path works on one machine but not another.

Recovery:

- Use a complete local model directory when offline behavior is required.
- Pass `cache_dir` from runtime configuration or rely on standard Hugging Face
  cache variables; do not hard-code machine-specific paths in skill code.
- Remember that the bundled smoke script does not load or download anything
  unless `--model-name` is supplied.
- If `--model-name` is a remote id, downloads are expected unless files are
  already cached.

## CPU/GPU Fallback And Precision

Symptom:

- A GPU run succeeds but a CPU run fails or is extremely slow.
- A CPU smoke check gives different dtype behavior from GPU.
- fp16 or bf16 runs fail on unsupported hardware.

Recovery:

- For smoke checks, pass `devices="cpu"`, `use_fp16=False`, and
  `use_bf16=False`.
- For production GPU runs, pass an explicit device such as `"cuda:0"` after the
  CPU smoke check succeeds.
- Use bf16 only on hardware that supports it.
- Reranker concrete classes disable fp16 on CPU before scoring. Embedders move
  CPU models to float precision.
- If `devices=None`, the package auto-selects accelerators before CPU, which is
  useful for production but less predictable for debugging.

## Out Of Memory

Symptom:

- Runtime error or accelerator OOM during tokenization, padding, encode, or
  score computation.
- Batch size is internally reduced but the run remains slow or still fails.

Recovery:

1. Reduce `batch_size` explicitly.
2. Reduce `query_max_length`, `passage_max_length`, or reranker `max_length`.
3. Disable M3 `return_colbert_vecs` unless token-level vectors are required.
4. Prefer `return_dense=True, return_sparse=False, return_colbert_vecs=False`
   for a minimal M3 smoke check.
5. For decoder-only rerankers, use smaller batches than encoder rerankers.
6. Delete model objects or call cleanup helpers in long-running processes after
   large multi-device jobs.

## Output-Shape Misuse

Symptom:

- Matrix multiplication fails with a dict input.
- Reranker sorting fails because a score is nested or scalar.
- A single input returns a 1-D vector where downstream code expects 2-D.

Recovery:

- Base embedders return arrays or tensors; M3 returns a dict. Use
  `m3_output["dense_vecs"]` before dense matrix multiplication.
- For a single base embedder input, wrap the text in a list to force a 2-D
  output: `model.encode_queries([query])`.
- For M3 single-string ColBERT output, normalize the shape before indexing;
  a string input can return one array instead of a list of arrays.
- Standard rerankers return a flat list of floats. Layerwise/lightweight
  rerankers can return a list of score lists when multiple cutoff layers are
  requested. Pick one layer or combine layers intentionally.
- M3 `compute_score` returns a dict of mode names to score lists for batch
  input, but values can be scalars for one input pair.

## Score-Mode Misuse

Symptom:

- Dense, sparse, and reranker scores are combined without comparable scale.
- `normalize=True` changes ranking behavior unexpectedly.
- M3 weighted scores look wrong.

Recovery:

- Treat base embedder similarity, M3 sparse/ColBERT scores, and reranker logits
  as different signals. Calibrate before adding them in production code.
- Use `normalize=True` for rerankers only when the consumer expects sigmoid
  scores in the 0-1 range. Raw logits are fine for sorting within one model.
- For M3 `weights_for_different_modes`, use order `[dense, sparse, colbert]`.
- Check that `return_sparse=True` before using `lexical_weights` and
  `return_colbert_vecs=True` before using `colbert_vecs`.

## Instruction Misuse

Symptom:

- Passage embeddings are much worse than expected.
- Query instructions appear twice in an encoded string.
- Custom checkpoint retrieval quality is poor even though encoding succeeds.

Recovery:

- For short-query to long-passage retrieval, put task instructions on queries
  through `query_instruction_for_retrieval` and call `encode_queries`.
- Use `encode_corpus` for passages so query instructions are not applied to
  documents.
- If text was manually prepended with an instruction, call `encode` or remove
  the configured query instruction to avoid double-instruction prompts.
- For custom checkpoints, match the instruction text and
  `query_instruction_format` used during training.

## Reranker Length Parameter Mismatch

Symptom:

- Passing `passage_max_length` to a reranker has no effect or raises an
  unexpected keyword error in custom wrappers.

Recovery:

- Use `query_max_length` for the query side and `max_length` for the passage or
  packed reranker length.
- Reserve `passage_max_length` for embedders.
