# Training and Data Troubleshooting

## `uv sync` from the repo root does not create the training env

Training is a separate project. Run:

```bash
cd train
uv sync
```

Do not expect root `pixelrag[index]` or `pixelrag[serve]` extras to satisfy training dependencies.

## CUDA or cuDNN mismatch

The training project pins torch/transformers/cuDNN versions. If CUDA import or allocation fails:

- Confirm the selected Python version is supported.
- Confirm the CUDA wheel source is used.
- Run a tiny torch CUDA allocation before training.
- Avoid mixing packages from an older root environment.

## QA score is zero or blank

Training can be healthy while evaluation grading fails. Check:

- `OPENAI_API_KEY` is set.
- `OPENAI_BASE_URL` matches the key's required region/provider.
- The vLLM reader is reachable and serving the expected model.
- Eval JSONL contains reader answers rather than empty/closed-book fallbacks.
- W&B/offline logging did not hide local eval outputs.

## Dataset paths do not resolve

JSONL image paths are often relative to the dataset directory. After extracting shards, verify that each `chunk_path` or image path exists relative to the expected data root. Use symlinks carefully when moving images to local SSD.

## Hard-negative mining returns poor negatives

- Confirm the search API is serving the intended index/model/adapter.
- Check `n_docs`, margin/filter mode, and whether positive chunks are excluded correctly.
- Validate `positive_score` and `positive_rank` fields on a small sample.

## LLM filtering costs too much

Run test-first or limited batches, lower concurrency, and record estimated token/API cost before full-scale filtering. Do not silently run 100k-row filtering jobs.

## HF downloads/uploads are slow or rate-limited

Set an HF token when permitted. Keep large shard downloads on fast local storage and verify free disk before extraction.

## Gradient or distributed tests fail

Training tests may require multi-GPU, exact package versions, or distributed launch semantics. Treat them as optional native verification unless the user specifically requests training-code maintenance.
