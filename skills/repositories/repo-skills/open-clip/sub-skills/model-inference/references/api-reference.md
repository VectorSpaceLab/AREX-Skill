# API Reference

This reference captures the OpenCLIP inference APIs verified from package source and tests. Prefer these public `open_clip` entry points over reaching into private modules.

## Discovery APIs

### `open_clip.list_models()`

Returns a list of built-in model architecture names registered from OpenCLIP config files. Use it before loading a user-supplied architecture name.

```python
import open_clip
models = open_clip.list_models()
```

Installed inspection found 180 built-in configs in this checkout.

### `open_clip.list_pretrained(as_str=False)`

Returns all known pretrained `(model_name, tag)` pairs by default, or strings like `"ViT-B-32:laion2b_s34b_b79k"` when `as_str=True`.

```python
pairs = open_clip.list_pretrained()
strings = open_clip.list_pretrained(as_str=True)
```

Installed inspection found 200 pretrained pairs in this checkout. Additional helpers:

- `open_clip.list_pretrained_tags_by_model(model)` returns tags for one architecture.
- `open_clip.list_pretrained_models_by_tag(tag)` returns architectures supporting one tag.
- `open_clip.is_pretrained_cfg(model, tag)` checks whether a model/tag pair is known.
- `open_clip.get_pretrained_cfg(model, tag)` returns the config metadata used for download/preprocess merging.

## Model Creation APIs

### `open_clip.create_model(...)`

Verified signature:

```python
create_model(
    model_name,
    pretrained=None,
    load_weights=True,
    precision="fp32",
    device="cpu",
    force_quick_gelu=False,
    force_custom_text=False,
    force_patch_dropout=None,
    force_image_size=None,
    force_preprocess_cfg=None,
    force_context_length=None,
    force_naflex_vision=False,
    pretrained_image=False,
    pretrained_text=True,
    pretrained_image_path=None,
    pretrained_text_path=None,
    pretrained_audio_path=None,
    cache_dir=None,
    output_dict=None,
    require_pretrained=False,
    weights_only=True,
    **model_kwargs,
)
```

Return: a `torch.nn.Module`, usually `open_clip.CLIP`, `open_clip.CustomTextCLIP`, `open_clip.CoCa`, `open_clip.CLAP`, `open_clip.NaFlexGenLip`, or `open_clip.NaFlexGenLap` depending on config. This sub-skill covers image/text CLIP-style and CoCa inference; route audio and generative NaFlex cases to sibling skills.

Identifier rules:

- Built-in name, e.g. `"ViT-B-32"`: load architecture config from OpenCLIP. `pretrained` may be `None`, a known tag, or a local checkpoint file path.
- `"hf-hub:org/repo"`: fetch `open_clip_config.json` and default weights from Hugging Face Hub. The `pretrained` argument is ignored.
- `"local-dir:/path/to/dir"`: read `/path/to/dir/open_clip_config.json` and discover a colocated checkpoint. The `pretrained` argument is ignored.

Important behavior:

- `load_weights=False` skips an otherwise resolved checkpoint path and is the safest no-download/no-weight-load path for shape smoke tests.
- `require_pretrained=True` raises if no full CLIP checkpoint loads; tower-specific weights do not satisfy it.
- `pretrained_image`, `pretrained_text`, and `pretrained_*_path` are tower-specific and useful for advanced partial initialization, not ordinary CLIP checkpoint loading.
- `force_image_size` overrides the vision config and may call `model.visual.set_input_size(...)` for timm towers.
- `force_context_length` overrides text config context length; pass the same context length to `get_tokenizer` to keep token tensors aligned.
- `force_custom_text=True` routes compatible configs through `CustomTextCLIP`; modern/variable text configs select custom text automatically.
- `output_dict=True` sets `model.output_dict=True` when supported.
- `weights_only=True` is the safer default for `torch.load` checkpoint files.

### `open_clip.create_model_and_transforms(...)`

Verified signature highlights:

```python
create_model_and_transforms(
    model_name,
    pretrained=None,
    load_weights=True,
    precision="fp32",
    device="cpu",
    force_quick_gelu=False,
    force_custom_text=False,
    force_patch_dropout=None,
    force_image_size=None,
    force_context_length=None,
    force_naflex_vision=False,
    image_mean=None,
    image_std=None,
    image_interpolation=None,
    image_resize_mode=None,
    aug_cfg=None,
    audio_aug_cfg=None,
    pretrained_image=False,
    pretrained_text=True,
    pretrained_image_path=None,
    pretrained_text_path=None,
    pretrained_audio_path=None,
    cache_dir=None,
    output_dict=None,
    weights_only=True,
    **model_kwargs,
)
```

Return: `(model, preprocess_train, preprocess_val)`.

Use this as the default inference constructor because it returns the validation/inference transform derived from the model and pretrained metadata. `preprocess_val` is usually a callable accepting a PIL image or tensor and returning a normalized CHW tensor; if NaFlex augmentation is requested it can be a factory, which belongs in the NaFlex sibling skill.

Preprocess override arguments:

- `image_mean`, `image_std`: per-channel normalization.
- `image_interpolation`: `"bicubic"`, `"bilinear"`, or `"random"`; random falls back to bicubic for inference transform construction.
- `image_resize_mode`: `"shortest"`, `"longest"`, or `"squash"`; only affects inference preprocessing.
- `aug_cfg`: training transform augmentation config; avoid for basic inference unless deliberately constructing training transforms.

### `open_clip.create_model_from_pretrained(...)`

Verified behavior: convenience wrapper around `create_model(..., require_pretrained=True)` plus an optional inference transform.

```python
model, preprocess = open_clip.create_model_from_pretrained(
    "ViT-B-32",
    pretrained="openai",
    device="cpu",
    return_transform=True,
)
```

Return: `(model, preprocess)` when `return_transform=True`; otherwise only `model`. Use this when pretrained weights are mandatory. Use `create_model_and_transforms(..., pretrained=None, load_weights=False)` for offline smoke checks.

## Tokenizer APIs

### `open_clip.get_tokenizer(model_name="", context_length=None, cache_dir=None, **kwargs)`

Returns a tokenizer callable selected from model config:

- Built-in configs choose `SimpleTokenizer`, `SigLipTokenizer`, HF tokenizers, or modern/tiktoken tokenizers based on `text_cfg`.
- `hf-hub:` tries to fetch model config; if unavailable, it can fall back to the HF model id for tokenizer selection.
- `local-dir:` requires a directory containing `open_clip_config.json`; if the text config names an HF tokenizer, tokenizer files are expected in that directory.
- `context_length` overrides config/default tokenizer length. Match it to `force_context_length` on the model.

The returned callable typically accepts a string or list of strings and returns a `torch.LongTensor` of token ids shaped `[batch, context_length]` for fixed-length tokenizers. Some modern variable-text tokenizers support non-padded outputs and collators; keep ordinary CLIP inference on padded fixed-length tensors unless intentionally using modern text features.

### `open_clip.tokenize(texts, context_length=77)`

Legacy simple tokenizer helper returning a `torch.LongTensor`. Use `get_tokenizer(model_name)` for model-specific tokenizers, especially SigLIP, HF text towers, modern text configs, `hf-hub:`, or `local-dir:` models.

```python
tokenizer = open_clip.get_tokenizer("ViT-B-32")
text = tokenizer(["a diagram", "a dog", "a cat"])
```

Special-token validation: `get_tokenizer` validates config/tokenizer `eos_id` and `pad_id` for eos/argmax pooling and variable text. Errors here usually mean the model config and tokenizer files do not match.

## Image Transform APIs

### `open_clip.image_transform(...)`

Public transform constructor:

```python
image_transform(
    image_size,
    is_train,
    mean=None,
    std=None,
    resize_mode=None,
    interpolation=None,
    fill_color=0,
    aug_cfg=None,
)
```

Return: a torchvision-style callable. For inference, prefer `is_train=False`. Valid `resize_mode` values are `"shortest"`, `"longest"`, and `"squash"`; valid interpolation values are `"bicubic"`, `"bilinear"`, and `"random"`.

For model-specific inference, prefer `create_model_and_transforms` or `open_clip.get_model_preprocess_cfg(model)` followed by a transform created from the returned config. Some pretrained tags override mean/std, and those overrides are merged automatically by `create_model_and_transforms`.

## Inference Contracts

### CLIP and `CustomTextCLIP`

Core methods:

```python
image_features = model.encode_image(image_tensor, normalize=False)
text_features = model.encode_text(text_tokens, normalize=False)
image_logits, text_logits = model.get_logits(image_tensor, text_tokens)
out = model(image=image_tensor, text=text_tokens)
```

Contracts:

- `image_tensor` is usually `[batch, 3, H, W]`, after validation transform and on the same device as the model.
- `text_tokens` is usually `[batch, context_length]`, dtype `torch.long`, on the same device as the model.
- `encode_image` and `encode_text` return `[batch, embed_dim]`; pass `normalize=True` or normalize manually before cosine similarity.
- `forward` returns `(image_features, text_features, logit_scale)` by default, or adds `logit_bias` if present.
- With `output_dict=True`, `forward` returns keys such as `image_features`, `text_features`, `logit_scale`, and optional `logit_bias`.

Always call `model.eval()` for inference. Source README and tests note that models are created in train mode, which affects BatchNorm and stochastic depth in some architectures.

### CoCa

`open_clip.CoCa` supports CLIP-like feature extraction and multimodal decoding, with caveats:

- `encode_image(images, normalize=True)` and `encode_text(text, normalize=True)` return normalized `[batch, embed_dim]` features by default.
- `forward(image=...)` returns a dict with `image_features` and `image_embs`.
- `forward(text=...)` returns a dict with `text_features`.
- `forward(image=..., text=...)` returns a dict including `image_features`, `text_features`, `logits`, `logit_scale`, and optional `logit_bias`.
- `forward_intermediates(output_logits=True)` is not implemented for CoCa.
- `generate(...)` requires `transformers` and manages eval mode internally during generation.
- CoCa training label shifting now belongs to the training task, not `coca_model.forward()`; do not assume forward slices captions for labels.

## Device and Precision

- Safe default: `precision="fp32", device="cpu"`.
- CUDA inference: move inputs to the same device and use a CUDA device string, e.g. `device="cuda"`.
- Avoid `fp16` on CPU. Use `fp32` on CPU; use `fp16`, `bf16`, `pure_fp16`, or `pure_bf16` only when the target device and operations support them.
- `torch.autocast("cuda")` is appropriate only on CUDA. Do not copy README snippets using CUDA autocast into CPU-only scripts without guarding device type.

## Local Checkpoints and Config Directories

- Built-in architecture plus local checkpoint file: `create_model_and_transforms("ViT-B-32", pretrained="/file/open_clip_pytorch_model.bin")`.
- Hugging Face repo with config/weights: `create_model_and_transforms("hf-hub:org/repo", cache_dir=...)`; `pretrained` is ignored.
- Local exported repo directory: `create_model_and_transforms("local-dir:/path/to/dir")`; the directory must contain `open_clip_config.json` with a top-level `model_cfg` key and optional `preprocess_cfg`, plus checkpoint files if weights should load.
- To load only config from `local-dir:` without weights, pass `load_weights=False`.
