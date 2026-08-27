# API Reference: CLIP Loading and Inference

This reference summarizes the public `clip` package API needed for model loading and inference. It is self-contained and avoids relying on the original source checkout.

## Package Exports

`import clip` exposes:

- `clip.available_models() -> List[str]`
- `clip.load(name: str, device="cuda" if available else "cpu", jit: bool = False, download_root: str | None = None)`
- `clip.tokenize(texts: str | list[str], context_length: int = 77, truncate: bool = False)`

The package distribution/import name is `clip`, version `1.0`.

## Available Model Names

`clip.available_models()` returns these exact checkpoint names:

- `RN50`
- `RN101`
- `RN50x4`
- `RN50x16`
- `RN50x64`
- `ViT-B/32`
- `ViT-B/16`
- `ViT-L/14`
- `ViT-L/14@336px`

Use one of these names for automatic cache/download loading, or pass a local checkpoint path to `clip.load`.

## `clip.load`

Signature:

```python
model, preprocess = clip.load(name, device=device, jit=False, download_root=None)
```

Arguments:

- `name`: either one of `clip.available_models()` or a local checkpoint file path.
- `device`: a string or `torch.device`; defaults to CUDA when available, otherwise CPU.
- `jit`: `False` loads the Python/eager model, which is easier to inspect and modify; `True` loads the TorchScript/JIT archive when available.
- `download_root`: optional cache directory for named model downloads; defaults to the user CLIP cache.

Returns:

- `model`: a `torch.nn.Module` in eval mode.
- `preprocess`: a TorchVision transform that accepts a `PIL.Image` and returns a normalized tensor for that model.

Behavior:

- Named checkpoints are downloaded to the cache if missing and verified by SHA256.
- If a cached file exists but the checksum differs, CLIP warns and re-downloads it.
- If a download finishes with a mismatched checksum, CLIP raises a `RuntimeError`.
- If `name` is neither a known model name nor an existing file, CLIP raises a `RuntimeError` that includes valid model names.
- If `jit=True` is requested for a non-JIT state dict, CLIP warns and loads it as a non-JIT model.
- On CPU with eager loading, CLIP converts the model to `float32`; GPU eager weights are generally converted for fp16-compatible inference.

## Preprocessing Transform

The returned `preprocess` transform performs model-specific image preparation:

1. Resize with bicubic interpolation to the model input resolution.
2. Center crop to the model input resolution.
3. Convert image to RGB.
4. Convert to a tensor in `C x H x W` layout.
5. Normalize with CLIP image mean `(0.48145466, 0.4578275, 0.40821073)` and std `(0.26862954, 0.26130258, 0.27577711)`.

Use `preprocess(Image.open(path)).unsqueeze(0).to(device)` for a single image. Do not pass raw PIL images or unnormalized tensors directly into the model.

## `clip.tokenize`

Signature:

```python
tokens = clip.tokenize(texts, context_length=77, truncate=False)
```

Behavior and returns:

- Accepts a single string or a list of strings.
- Returns a two-dimensional tensor with shape `[number_of_texts, context_length]`.
- Uses context length `77` for CLIP models.
- Returns `int32` on modern PyTorch and `int64` on older PyTorch releases.
- Raises `RuntimeError` when a text is too long unless `truncate=True` is passed.

Move tokens to the same device as the model inputs with `tokens.to(device)` before inference.

## Model Methods and Tensor Shapes

The model returned by `clip.load` supports:

```python
image_features = model.encode_image(image)
text_features = model.encode_text(text)
logits_per_image, logits_per_text = model(image, text)
```

Expected inputs:

- `image`: tensor with shape `[image_batch, 3, input_resolution, input_resolution]`, produced by `preprocess` and moved to the model device.
- `text`: token tensor with shape `[text_batch, 77]`, produced by `clip.tokenize` and moved to the model device.

Returns:

- `encode_image(image)`: image feature tensor with shape `[image_batch, embed_dim]`.
- `encode_text(text)`: text feature tensor with shape `[text_batch, embed_dim]`.
- `model(image, text)`: `logits_per_image` with shape `[image_batch, text_batch]` and `logits_per_text` with shape `[text_batch, image_batch]`.

`model(image, text)` normalizes image/text features internally and scales cosine similarities by the learned logit scale. Apply `logits_per_image.softmax(dim=-1)` to get probabilities over labels for each image.

## Torch Hub Entrypoints

CLIP's Torch Hub interface exposes punctuation-normalized entrypoints for each model. Punctuation characters in model names are replaced by underscores:

| CLIP model | Torch Hub entrypoint |
| --- | --- |
| `RN50` | `RN50` |
| `RN101` | `RN101` |
| `RN50x4` | `RN50x4` |
| `RN50x16` | `RN50x16` |
| `RN50x64` | `RN50x64` |
| `ViT-B/32` | `ViT_B_32` |
| `ViT-B/16` | `ViT_B_16` |
| `ViT-L/14` | `ViT_L_14` |
| `ViT-L/14@336px` | `ViT_L_14_336px` |

Torch Hub entrypoints accept the same keyword arguments as `clip.load`, including `device`, `jit`, and `download_root`, and return `(model, preprocess)`. The hub module also exposes `tokenize()`, which returns the tokenizer function.

## Device and Dtype Notes

- Choose `device = "cuda" if torch.cuda.is_available() else "cpu"` unless a caller explicitly requests a device.
- Keep image tensors, text tokens, and model on the same device.
- Wrap inference in `with torch.no_grad():`.
- Use `model.eval()` if a workflow modifies model state, though `clip.load` already returns an eval-mode model.
- On CPU, prefer `jit=False` unless you specifically need TorchScript parity testing; CPU JIT archives are patched to use CPU and float32.
