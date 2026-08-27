# Troubleshooting: CLIP Loading and Inference

Use this guide for common install, import, loading, preprocessing, device, and network failures.

## Import or Installation Fails

Symptoms:

- `ModuleNotFoundError: No module named 'clip'`
- Import succeeds for a different package than expected.
- Missing dependencies such as `ftfy`, `regex`, `tqdm`, `torch`, or `torchvision`.

Fixes:

- Confirm the package imports with `python scripts/clip_smoke_check.py --json`.
- Install PyTorch and torchvision with versions compatible with the target CPU/CUDA runtime.
- Install CLIP and its small dependencies in the same Python environment used to run scripts.
- Avoid naming local files `clip.py`, which can shadow the package.

## Torch or TorchVision Compatibility Errors

Symptoms:

- Errors importing `torchvision.transforms`.
- CUDA runtime mismatch errors.
- Warnings recommending PyTorch `1.7.1` or newer.

Fixes:

- Use matching `torch` and `torchvision` builds for the same CUDA or CPU runtime.
- On CPU-only machines, install CPU builds and load with `device="cpu"`.
- If CUDA is present but unreliable, force `--device cpu` in helper scripts.

## Invalid Model Name

Symptom:

- `RuntimeError: Model <name> not found; available models = [...]`

Fixes:

- Use exact names from `clip.available_models()`.
- Remember that `ViT-B/32`, `ViT-B/16`, `ViT-L/14`, and `ViT-L/14@336px` include punctuation.
- If the value was meant to be a checkpoint, verify that the file path exists before passing it to `clip.load`.
- For Torch Hub, use punctuation-normalized entrypoints such as `ViT_B_32`; for direct `clip.load`, use the original model name such as `ViT-B/32`.

## Network Restrictions

Symptoms:

- Download hangs or fails.
- HTTP, TLS, proxy, or DNS errors while loading a named model.
- The environment must not download model or dataset files.

Fixes:

- Run `python scripts/clip_smoke_check.py --json` for no-download validation.
- Use a user-provided local checkpoint path with `clip.load(path, device=device)`.
- If named checkpoints are already cached, use the named model with the correct `download_root`.
- Do not run dataset examples or Torch Hub loading unless the user permits network access.

## Cache or Checksum Failures

Symptoms:

- Warning that an existing cache file checksum does not match.
- `RuntimeError: Model has been downloaded but the SHA256 checksum does not not match`.
- Error that a cache target exists and is not a regular file.

Fixes:

- Treat checksum mismatch as a corrupt or partial checkpoint.
- Delete or replace the bad cache file only with user approval when mutating shared caches.
- Choose a clean `download_root` when the cache path collides with a directory or special file.
- Retry downloads only when the user allows network access.

## CPU/GPU Device Mismatch

Symptoms:

- `Expected all tensors to be on the same device`.
- CUDA availability differs from the requested device.
- Out-of-memory errors on GPU.

Fixes:

- Set `device = "cuda" if torch.cuda.is_available() else "cpu"` unless the user specifies otherwise.
- Move both image tensors and text tokens to the same device: `image.to(device)` and `text.to(device)`.
- Use `--device cpu` for debugging or low-memory environments.
- Keep `with torch.no_grad():` around inference.

## JIT Fallback or TorchScript Warnings

Symptoms:

- Warning that a file is not a JIT archive and is being loaded as a state dict.
- TorchScript graph/device issues in older runtimes.

Fixes:

- Prefer `jit=False` unless the user needs JIT parity.
- Use `jit=True` only for compatible CLIP JIT checkpoint archives.
- If a local checkpoint is a state dict, the warning is expected and CLIP falls back to eager loading.
- On CPU, CLIP patches JIT archives to use CPU and float32, but eager loading is usually simpler.

## Image Preprocessing Mistakes

Symptoms:

- Shape errors from `model.encode_image` or `model(image, text)`.
- Poor predictions from raw or incorrectly normalized tensors.
- PIL or image mode errors.

Fixes:

- Always use the `preprocess` returned by the same `clip.load` call as the model.
- Pass a `PIL.Image` to `preprocess`; it handles RGB conversion.
- Add a batch dimension with `.unsqueeze(0)` for one image.
- Move the preprocessed tensor to the model device.
- Expected image shape is `[batch, 3, input_resolution, input_resolution]`.

## Text Tokenization Issues

Symptoms:

- `RuntimeError` that input text is too long for context length `77`.
- Shape mismatch in `encode_text`.

Fixes:

- Tokenize with `clip.tokenize(labels)` and move the result to the model device.
- Keep labels concise or pass `truncate=True` when truncation is acceptable.
- Expected token shape is `[number_of_labels, 77]`.

## Probability Interpretation

Symptoms:

- User treats raw logits as probabilities.
- Top label looks wrong because labels are underspecified.

Fixes:

- Convert logits with `logits_per_image.softmax(dim=-1)` for probabilities over the provided labels.
- Remember probabilities are conditional over the candidate labels supplied, not calibrated open-world probabilities.
- For prompt wording, templates, and ensembling, route to [prompt-engineering](../../prompt-engineering/).
