# Model Selection

OpenCLIP separates architecture choice from weight source. Pick both deliberately.

## Selection Checklist

1. Choose a model architecture from `open_clip.list_models()`.
2. Choose a pretrained source from `open_clip.list_pretrained_tags_by_model(model)` or use `pretrained=None` for random initialization.
3. Check whether the model requires optional dependencies such as `timm`, `transformers`, `tokenizers`, `tiktoken`, `safetensors`, or `huggingface_hub`.
4. Match image size, context length, tokenizer, and QuickGELU settings to the chosen checkpoint.
5. Use `create_model_and_transforms` unless you have a reason to build transforms manually.
6. Run a no-download shape/finite smoke test before interpreting model quality.

## Architecture Names

Built-in model names include CLIP-style ResNets, ViTs, ConvNeXt/EVA/timm-backed variants, SigLIP-style configs, CoCa configs, modern text configs, and additional experimental families. Installed inspection found 180 registered configs, but availability can vary by package version.

Practical patterns:

- `"ViT-B-32"`: common baseline with many tags.
- `"ViT-B-32-quickgelu"`: use when the checkpoint was trained with QuickGELU and a quickgelu config exists.
- `"roberta-ViT-B-32"` or similar HF-text models: require `transformers` and model-specific tokenizers.
- `"coca_ViT-B-32"`: CoCa image/text embeddings plus multimodal decoder behavior; forward returns dicts.
- Modern text models: require careful tokenizer/special-token matching and often `force_custom_text` is automatic.

Use `open_clip.get_model_config(model_name)` to inspect `vision_cfg`, `text_cfg`, `quick_gelu`, `custom_text`, `multimodal_cfg`, `audio_cfg`, and image size before loading weights.

## Pretrained Tags

`pretrained` is meaningful only for built-in model names. It may be:

- `None`: no full CLIP checkpoint; safe for offline shape tests but not semantic results.
- Known tag such as `"openai"`, `"laion2b_s34b_b79k"`, or `"datacomp_xl_s13b_b90k"` when supported by the architecture.
- A local checkpoint file path compatible with the chosen architecture.

Check tags before loading:

```python
import open_clip
model = "ViT-B-32"
print(open_clip.list_pretrained_tags_by_model(model))
```

If a tag is unknown, OpenCLIP raises with the available tags for that model. Tags are normalized internally toward lowercase/underscore forms, but agents should copy tags from `list_pretrained()` to avoid surprises.

## QuickGELU Compatibility

Many older OpenCLIP/OpenAI checkpoints were trained with QuickGELU. Current model defaults often use native `torch.nn.GELU` for speed. A mismatch can load but produce weaker results.

Decision rules:

- Prefer the `-quickgelu` architecture variant when `list_pretrained()` exposes that model/tag pair.
- Use `force_quick_gelu=True` only when there is no clearer matching architecture name and you know the checkpoint was trained with QuickGELU.
- OpenAI pretrained weights default to QuickGELU-compatible configs.
- If results are unexpectedly weak but loading succeeds, inspect `open_clip.get_pretrained_cfg(model, tag).get("quick_gelu")` and `open_clip.get_model_config(model).get("quick_gelu")`.
- Do not dismiss QuickGELU warnings during evaluation or retrieval quality diagnosis.

Difficult case: a user loads `"ViT-B-32"` with a QuickGELU-trained local checkpoint and gets poor rankings. Try `"ViT-B-32-quickgelu"` or `force_quick_gelu=True`, rerun embedding normalization and a known probe image/text set, then compare.

## Hugging Face Hub vs Local Directory vs Local Checkpoint

### Use `hf-hub:` when

- The user names an OpenCLIP-compatible HF repository.
- The repository contains `open_clip_config.json` and OpenCLIP weights.
- Network/cache access is allowed.
- The model may need HF tokenizer files from the same repository.

Example:

```python
model_name = "hf-hub:org/repo"
model, _, preprocess = open_clip.create_model_and_transforms(model_name, cache_dir=".cache/open_clip")
tokenizer = open_clip.get_tokenizer(model_name, cache_dir=".cache/open_clip")
```

`pretrained` is ignored for `hf-hub:`.

### Use `local-dir:` when

- The user has an exported directory with `open_clip_config.json`.
- Config, weights, preprocess settings, and tokenizer files should travel together.
- Network access should not be required.

Example:

```python
model_name = "local-dir:my-openclip-export"
model, _, preprocess = open_clip.create_model_and_transforms(model_name)
tokenizer = open_clip.get_tokenizer(model_name)
```

`pretrained` is ignored for `local-dir:`. Missing `open_clip_config.json` or missing `model_cfg` is a hard error.

### Use a local checkpoint file when

- The user has only a `.pt`, `.pth`, `.bin`, `.safetensors`, `.npz`, or `.npy` checkpoint file.
- You know the correct built-in architecture name.
- The tokenizer and preprocess should be derived from the built-in model/tag or explicit overrides.

Example:

```python
model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32",
    pretrained="open_clip_pytorch_model.bin",
)
```

For user-provided checkpoint directories, first look for `open_clip_config.json`. If present, prefer `local-dir:`. If the directory only contains a weight file and no config, ask for or infer the matching built-in architecture before using `pretrained=<file>`.

## Tokenizer Selection

Use `open_clip.get_tokenizer(model_name)`, not `open_clip.tokenize`, unless the model is known to use the legacy simple tokenizer.

Reasons:

- SigLIP names choose SigLIP tokenizer variants.
- HF text towers need `transformers`/HF tokenizer files.
- Modern text configs can use tiktoken or variable-length text settings.
- `local-dir:` models may expect tokenizer files inside the export directory.
- `get_tokenizer` validates `eos_id` and `pad_id` against tokenizer metadata.

If `force_context_length` is passed during model creation, pass the same value as `context_length` to `get_tokenizer`.

## Image Preprocess Selection

Use the validation transform from `create_model_and_transforms` for inference. It reflects:

- Model visual image size.
- Pretrained metadata mean/std overrides.
- Interpolation and resize mode.
- User overrides such as `image_mean`, `image_std`, `image_interpolation`, and `image_resize_mode`.

Manual `image_transform(...)` is useful for custom workflows, but it can accidentally miss checkpoint-specific preprocessing. One documented pretrained family uses `[0.5, 0.5, 0.5]` mean/std instead of OpenAI defaults, and `create_model_and_transforms` handles that automatically.

## Device and Precision Selection

Safe defaults:

- CPU: `device="cpu", precision="fp32"`.
- CUDA: `device="cuda"`, optionally `precision="fp16"` or `"bf16"` if the GPU supports it.
- Avoid `fp16` and CUDA autocast on CPU.
- Move all image/text tensors to the model device before encoding.

Use `torch.no_grad()` or `torch.inference_mode()` for inference. Always call `model.eval()` before comparing scores.

## CoCa Selection

Choose CoCa when the task needs a CoCa architecture or caption-generation behavior, not just CLIP embeddings. CoCa still supports `encode_image` and `encode_text`, but:

- Features are normalized by default in CoCa encoders.
- `forward` returns dictionaries, not CLIP tuples.
- Generation requires `transformers`.
- Training label-shift behavior belongs in training tasks, not inference forward calls.

For ordinary image/text embedding search or zero-shot classification, a standard CLIP/CustomTextCLIP model is usually simpler.

## Output Format Selection

- Use `encode_image` and `encode_text` for embeddings.
- Use `model.get_logits(image, text)` for paired logits on CLIP/CustomTextCLIP.
- Use `output_dict=True` when named fields are easier than tuple unpacking.
- For CoCa, expect dict outputs without needing `output_dict=True`.

## Routing Reminders

- Model loading and embeddings: this sub-skill.
- Training/fine-tuning/checkpoint resume: `../training/SKILL.md`.
- Audio CLAP inputs: `../audio-clap/SKILL.md`.
- NaFlex patch dictionaries, GenLIP, GenLAP: `../naflex-generative/SKILL.md`.
- Zero-shot classifier prompts, retrieval pipelines, conversion/export: `../evaluation-conversion/SKILL.md`.
