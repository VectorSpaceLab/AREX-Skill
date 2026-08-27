# Workflows

These workflows are self-contained OpenCLIP inference recipes. They intentionally avoid relying on source-repo examples, notebooks, or local checkout paths.

## No-Download Smoke Inference

Use this when validating an installation, API shape, model config, tokenizer compatibility, and preprocessing without downloading weights.

```python
import torch
from PIL import Image
import open_clip

model_name = "ViT-B-32"
device = "cpu"
model, _, preprocess = open_clip.create_model_and_transforms(
    model_name,
    pretrained=None,
    load_weights=False,
    device=device,
)
model.eval()
tokenizer = open_clip.get_tokenizer(model_name)

image = Image.new("RGB", (256, 256), color=(128, 64, 32))
image_tensor = preprocess(image).unsqueeze(0).to(device)
text = tokenizer(["a synthetic image", "a blank square"]).to(device)

with torch.no_grad():
    image_features = model.encode_image(image_tensor, normalize=True)
    text_features = model.encode_text(text, normalize=True)
    logits = 100.0 * image_features @ text_features.T

assert image_features.shape[0] == 1
assert text_features.shape[0] == 2
assert torch.isfinite(logits).all()
```

Do not interpret random-init logits semantically. This workflow verifies plumbing only.

## Pretrained Tag Inference

Use a built-in model name plus a tag from `open_clip.list_pretrained()`.

```python
import torch
from PIL import Image
import open_clip

model_name = "ViT-B-32"
pretrained = "laion2b_s34b_b79k"
device = "cuda" if torch.cuda.is_available() else "cpu"

model, _, preprocess = open_clip.create_model_and_transforms(
    model_name,
    pretrained=pretrained,
    device=device,
)
model.eval()
tokenizer = open_clip.get_tokenizer(model_name)

image = preprocess(Image.open("image.jpg")).unsqueeze(0).to(device)
text = tokenizer(["a diagram", "a dog", "a cat"]).to(device)

with torch.no_grad():
    image_features = model.encode_image(image, normalize=True)
    text_features = model.encode_text(text, normalize=True)
    probs = (100.0 * image_features @ text_features.T).softmax(dim=-1)
```

Rules:

- Check `open_clip.list_pretrained_tags_by_model(model_name)` before selecting a tag.
- `create_model_and_transforms` merges tag-specific preprocessing. Do not reconstruct mean/std by hand unless you know the checkpoint metadata.
- Call `model.eval()` before inference; models are created in train mode.
- Use CUDA autocast only under a CUDA guard.

## Pretrained Required Workflow

Use `create_model_from_pretrained` when the task must fail if weights are not available.

```python
model, preprocess = open_clip.create_model_from_pretrained(
    "ViT-B-32",
    pretrained="openai",
    device="cpu",
)
model.eval()
```

This wrapper sets `require_pretrained=True`. It is not the right choice for offline shape smoke tests.

## Local Checkpoint File Workflow

Use this when the user provides a checkpoint file but wants a built-in architecture config.

```python
model_name = "ViT-B-32"
checkpoint_file = "open_clip_pytorch_model.bin"
model, _, preprocess = open_clip.create_model_and_transforms(
    model_name,
    pretrained=checkpoint_file,
    device="cpu",
    weights_only=True,
)
model.eval()
tokenizer = open_clip.get_tokenizer(model_name)
```

Checklist:

- The architecture name must match the checkpoint layout.
- For old OpenAI-style weights, use the matching `-quickgelu` model name or `force_quick_gelu=True` if needed.
- If the checkpoint was exported with a non-default image size or text context, pass `force_image_size` and `force_context_length` and keep tokenizer context length in sync.
- If loading only an image or text tower, use `pretrained_image_path` or `pretrained_text_path` and expect partial-load warnings.

## Hugging Face Hub Workflow

Use an `hf-hub:` model identifier when the Hub repository contains OpenCLIP-compatible `open_clip_config.json` and weights.

```python
model, _, preprocess = open_clip.create_model_and_transforms(
    "hf-hub:laion/CLIP-ViT-B-32-laion2B-s34B-b79K",
    device="cpu",
    cache_dir=".cache/open_clip",  # optional project cache
)
model.eval()
tokenizer = open_clip.get_tokenizer(
    "hf-hub:laion/CLIP-ViT-B-32-laion2B-s34B-b79K",
    cache_dir=".cache/open_clip",
)
```

Rules:

- `pretrained=` is ignored for `hf-hub:` model names.
- `huggingface_hub` is required for model/config downloads.
- `transformers`, `tokenizers`, or `tiktoken` may be required depending on the text tower.
- Use `cache_dir` for repeatability and explicit cache placement.
- If network access is disallowed, do not use `hf-hub:` unless the cache already contains all needed files and the environment supports offline HF behavior.

## Local Directory Workflow

Use `local-dir:` when a complete OpenCLIP export directory is available.

Expected layout:

```text
my-openclip-model/
  open_clip_config.json
  open_clip_pytorch_model.bin       # or supported safetensors/checkpoint file
  tokenizer files as needed         # for HF/tiktoken text towers
```

Usage:

```python
model_name = "local-dir:my-openclip-model"
model, _, preprocess = open_clip.create_model_and_transforms(model_name, device="cpu")
model.eval()
tokenizer = open_clip.get_tokenizer(model_name)
```

Rules:

- `open_clip_config.json` must contain a top-level `model_cfg` key and may contain `preprocess_cfg`.
- `pretrained=` is ignored for `local-dir:` model names.
- Use `load_weights=False` to test only config/model construction.
- Relative `local-dir:` paths are resolved from the current process working directory, so prefer explicit project-relative paths in scripts.
- If tokenizer files are referenced by config and `schema == local-dir`, OpenCLIP expects them in the local directory.

## Tokenizer and Context-Length Workflow

When overriding context length, keep model and tokenizer aligned.

```python
context_length = 128
model = open_clip.create_model(
    "ViT-B-32",
    pretrained=None,
    load_weights=False,
    force_context_length=context_length,
)
model.eval()
tokenizer = open_clip.get_tokenizer("ViT-B-32", context_length=context_length)
text = tokenizer(["a longer prompt"])  # shape [1, 128]
```

If `get_tokenizer` raises about `eos_id`, `pad_id`, or `pad_token_id`, treat it as a model-config/tokenizer mismatch, not as a warning to suppress.

## Output-Dict Workflow

Use `output_dict=True` when downstream code wants named outputs.

```python
model = open_clip.create_model(
    "ViT-B-32",
    pretrained=None,
    load_weights=False,
    output_dict=True,
).eval()

image = torch.randn(1, 3, model.visual.image_size, model.visual.image_size)
text = open_clip.get_tokenizer("ViT-B-32")(["a test"])

with torch.no_grad():
    out = model(image=image, text=text)

image_features = out["image_features"]
text_features = out["text_features"]
logit_scale = out["logit_scale"]
```

For CLIP/CustomTextCLIP without `output_dict=True`, `forward` returns a tuple. CoCa forward returns a dict by design.

## Embedding Extraction Workflow

Use normalized features for cosine similarity/retrieval scores; store raw features only if a downstream method requires them.

```python
with torch.no_grad():
    image_features = model.encode_image(image_tensor, normalize=True)
    text_features = model.encode_text(text_tokens, normalize=True)
    scores = image_features @ text_features.T
```

Batching guidance:

- Preprocess PIL images to tensors first, then stack with `torch.stack`.
- Move both image and text tensors to the same device as the model.
- Use `torch.no_grad()` or `torch.inference_mode()`.
- Keep model in eval mode for stable BatchNorm/stochastic-depth behavior.

Large-scale retrieval pipelines, zero-shot classifier templates, and conversion/export workflows belong in `../evaluation-conversion/SKILL.md`.

## Model and Preprocess Inspection Workflow

Inspect config before forcing overrides.

```python
import open_clip

model_name = "ViT-B-32"
print(open_clip.get_model_config(model_name))
print(open_clip.list_pretrained_tags_by_model(model_name))

model, _, preprocess = open_clip.create_model_and_transforms(model_name, pretrained=None, load_weights=False)
print(open_clip.get_model_preprocess_cfg(model))
print(open_clip.get_model_tokenize_cfg(model))
```

Use the model profile table as a selection reference for image size, widths, parameter counts, and FLOPs. Runtime skills should summarize selection criteria rather than depend on external tables being present.

## CoCa Inference Workflow

CoCa models can produce CLIP-like image/text embeddings and optional caption logits/generation.

```python
model, _, preprocess = open_clip.create_model_and_transforms(
    "coca_ViT-B-32",
    pretrained=None,
    load_weights=False,
    device="cpu",
)
model.eval()
tokenizer = open_clip.get_tokenizer("coca_ViT-B-32")

image = preprocess(Image.new("RGB", (256, 256))).unsqueeze(0)
text = tokenizer(["a synthetic image"])

with torch.no_grad():
    image_features = model.encode_image(image)  # normalized by default for CoCa
    text_features = model.encode_text(text)     # normalized by default for CoCa
    out = model(image=image, text=text)
```

Caveats:

- CoCa `forward` returns dicts; do not unpack it like basic CLIP tuples.
- CoCa `forward_intermediates(output_logits=True)` is not implemented.
- `model.generate(...)` requires `transformers` and generation-specific token ids/config.
- Training-time label shifting belongs to the CoCa training task; inference callers should handle labels/prompts explicitly.

## Safe Script Workflow

Run the bundled helper from the generated open-clip skill root:

```bash
python sub-skills/model-inference/scripts/inference_smoke.py --model ViT-B-32 --pretrained none --device cpu
```

Useful variants:

```bash
python sub-skills/model-inference/scripts/inference_smoke.py --model ViT-B-32 --force-context-length 64
python sub-skills/model-inference/scripts/inference_smoke.py --model ViT-B-32 --pretrained openai --allow-downloads
python sub-skills/model-inference/scripts/inference_smoke.py --model local-dir:my-openclip-model --pretrained none --load-weights
python sub-skills/model-inference/scripts/inference_smoke.py --list-models --list-pretrained
```

The helper refuses pretrained/HF download-prone modes unless `--allow-downloads` is passed. It still cannot guarantee that all cache layers are offline; use it as a safety guard, not a sandbox.
