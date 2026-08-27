# Workflows: CLIP Loading and Inference

These workflows cover safe import checks, one-image classification, feature encoding, local checkpoints, JIT choices, and cache/download handling.

## No-Download Validation

Use this when the user cannot access the network or only wants to confirm that CLIP imports and tokenizes correctly.

```bash
python scripts/clip_smoke_check.py --json
```

This checks package import, `available_models()`, `tokenize()`, tensor shape/dtype, and public `clip.load` signature without calling `clip.load` or downloading checkpoints.

A minimal inline version:

```python
import clip

print(clip.available_models())
tokens = clip.tokenize(["a diagram", "a dog"])
print(tokens.shape, tokens.dtype)
```

Expected token shape is `[2, 77]`. On modern PyTorch the dtype is usually `torch.int32`; older PyTorch may return `torch.int64`.

## Choose a Model

Start with `ViT-B/32` for general examples because it is common and relatively small. Use exact names from `clip.available_models()`:

```python
import clip
print("\n".join(clip.available_models()))
```

If the user provides an invalid name, show the valid names and ask whether they have a local checkpoint path. Local checkpoint loading uses the same `clip.load` entrypoint.

## Load a Named Checkpoint

```python
import torch
import clip

model_name = "ViT-B/32"
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load(model_name, device=device, jit=False, download_root=None)
```

Notes:

- Named models may download checkpoint files if they are not already cached.
- Pass `download_root` to control the cache location.
- Use `jit=False` for most agent-authored workflows because eager models are easier to debug.

## Load a Local Checkpoint

Use a local `.pt` checkpoint path when the network is unavailable or a checkpoint has already been staged by the user:

```python
import torch
import clip

checkpoint_path = "path/to/clip-checkpoint.pt"
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load(checkpoint_path, device=device, jit=False)
```

`clip.load` accepts the path only if it exists as a file. If the path is wrong, CLIP treats the value as an unknown model name and raises a `RuntimeError` listing valid named models.

## Preprocess One Image

```python
from PIL import Image

image = preprocess(Image.open("image.jpg")).unsqueeze(0).to(device)
```

Important details:

- Pass a `PIL.Image` to `preprocess`; it converts to RGB internally.
- Add the batch dimension with `.unsqueeze(0)`.
- Move the result to the same device used for the model.

## Score One Image Against Text Labels

```python
import torch
import clip
from PIL import Image

labels = ["a diagram", "a dog", "a cat"]
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)
image = preprocess(Image.open("image.jpg")).unsqueeze(0).to(device)
text = clip.tokenize(labels).to(device)

with torch.no_grad():
    logits_per_image, logits_per_text = model(image, text)
    probabilities = logits_per_image.softmax(dim=-1)

for label, probability in zip(labels, probabilities[0].cpu().tolist()):
    print(f"{label}: {probability:.4f}")
```

Use `scripts/image_text_similarity.py` for a reusable CLI version with `--model`, `--device`, `--download-root`, `--jit`, and `--top-k` arguments.

## Encode Image and Text Features

Use `encode_image` and `encode_text` when a workflow needs embeddings instead of direct logits:

```python
with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)

image_features = image_features / image_features.norm(dim=-1, keepdim=True)
text_features = text_features / text_features.norm(dim=-1, keepdim=True)
similarity = image_features @ text_features.T
```

For dataset-scale feature extraction and linear probes, route to [feature-evaluation](../../feature-evaluation/) rather than expanding that loop here.

## JIT Decision Guide

Use `jit=False` by default:

- Best for debugging, inspecting modules, adapting feature extraction, or CPU-only workflows.
- Loads state dict checkpoints into the Python `CLIP` module.
- Converts CPU eager models to float32.

Use `jit=True` only when the user specifically wants the TorchScript archive path or parity with native consistency checks:

- CLIP patches device constants in the JIT graph for the requested device.
- On CPU, CLIP patches dtype constants to float32.
- If the file is not a JIT archive, CLIP warns and falls back to state-dict eager loading.

A safe JIT/eager comparison should use already-available local or cached checkpoints and must not trigger large downloads unless the user explicitly allows them.

## Cache and Download Options

Named model loading uses URLs with SHA256 directory names and stores files under the CLIP cache by default. Control the cache explicitly with:

```python
model, preprocess = clip.load("ViT-B/32", download_root="path/to/cache", device=device)
```

Guidance:

- For offline environments, do not call `clip.load` with a named model unless the checkpoint is already cached or the user confirms that downloads are allowed.
- For restricted networks, prefer `clip_smoke_check.py` first, then ask the user to provide a local checkpoint path.
- If a cache file checksum fails, delete or replace the bad file and retry only when network access is allowed.
- If the cache path exists but is not a regular file, choose a different `download_root` or fix the path.

## Torch Hub Loading

When a user wants Torch Hub, use the punctuation-normalized entrypoint name from [api-reference.md](api-reference.md):

```python
import torch

model, preprocess = torch.hub.load("openai/CLIP", "ViT_B_32", device=device, jit=False)
tokenize = torch.hub.load("openai/CLIP", "tokenize")
```

Torch Hub can involve network and repository caching. For offline workflows, prefer direct package import plus a local checkpoint path.
