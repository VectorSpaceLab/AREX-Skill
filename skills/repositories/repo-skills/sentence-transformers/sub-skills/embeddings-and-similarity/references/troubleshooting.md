# Dense Embedding Troubleshooting

## Install and Import Failures

- `ModuleNotFoundError: sentence_transformers`: install with `pip install -U sentence-transformers` in Python 3.10+.
- Torch or Transformers version conflicts: verify PyTorch is installed for the intended CPU/GPU backend and that `transformers` satisfies the package requirement.
- CUDA requested but unavailable: confirm `torch.cuda.is_available()` before using `device="cuda"`; fall back to CPU for smoke tests.
- Private or gated model load errors: pass a valid Hugging Face token through configuration and keep `trust_remote_code=False` unless remote code is explicitly approved.

## Model Download, Cache, and Offline Failures

- `local_files_only=True` with an uncached model fails by design; provide a local model directory or pre-populate the cache.
- Unexpected network access usually means a model id was used without `local_files_only=True` or the cache is incomplete.
- Revision mismatches can load different pooling, prompts, or dimensions; pin `revision` for production.
- Avoid hardcoding cache folders in public scripts; make cache policy user-configurable.

## API Misuse

- A single string input can produce a one-vector result; wrap text in a list when downstream code expects a batch axis.
- `convert_to_numpy=True` and `convert_to_tensor=True` should not both be treated as independent outputs; pick one stable container for callers.
- Invalid `precision` values raise `ValueError`; supported values are `float32`, `int8`, `uint8`, `binary`, and `ubinary`.
- Quantized precision can break downstream libraries expecting float arrays; use `float32` until the scoring/index path supports quantized vectors.
- `truncate_dim` must be applied consistently to both sides of a similarity comparison and should not exceed the native embedding dimension.
- Token embeddings are not sentence embeddings; keep `output_value="sentence_embedding"` unless intentionally inspecting token-level output.

## Prompt and Similarity Problems

- Poor retrieval scores can come from using `encode` for a prompt-aware retrieval model; try `encode_query` and `encode_document`.
- Manual prompts must match the model's training convention; arbitrary instruction strings can move queries/documents out of the expected embedding space.
- Dot-product models often assume normalized embeddings; use `normalize_embeddings=True` or confirm the model already normalizes.
- `euclidean` and `manhattan` similarities are negative distances; sort descending, not ascending.
- `model.similarity(a, b)` returns all pairs; use `similarity_pairwise` only when aligned pair scores are desired.

## Backend and Service Limits

- ONNX/OpenVINO export, optimized model files, and backend-specific quantization belong in `../backend-export-optimization/`.
- External vector databases, FAISS indexes, semantic search chunking, and hard-negative mining belong in `../retrieval-and-utilities/`.
- Out-of-memory errors: reduce `batch_size`, truncate long inputs earlier, use smaller models, or move smoke validation to CPU.
- Slow inference: benchmark batch size and device before adding multiprocessing; process startup and serialization can dominate small jobs.

## Multimodal Failures

- Image/audio/video support requires both a model that supports the modality and the matching optional extras.
- Check `model.modalities` and `model.supports("image")`/`supports("audio")`/`supports("video")` before changing input code.
- Install `sentence-transformers[image]`, `[audio]`, or `[video]` as needed; audio/video decoder objects may also require `torchcodec`.
- For multimodal dicts, use only valid keys: `text`, `image`, `audio`, and `video`.
- Chat-style message inputs require a model exposing the `message` modality; ordinary text embedding models will not accept them.

## Smoke Script Symptoms

- `--help` should run without importing or downloading models.
- Missing `--model` exits with a clear message instead of defaulting to a network download.
- `--local-files-only` plus a remote id requires the model to already be cached; otherwise supply a local model directory.
- Shape or norm assertions failing usually indicate empty input, incompatible truncation, non-float precision, or a model that returns a specialized output.
