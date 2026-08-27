# Model Paths and Extra Configs

ComfyUI keeps a category-to-folder registry for model lookup. Loader nodes ask for a category such as `checkpoints`, `loras`, `vae`, or `controlnet`; ComfyUI then searches that category's registered folders and filters by allowed extensions.

## Built-in Search Layout

With the default base directory, common folders are under `models/`:

| Category | Default folders | Notes |
| --- | --- | --- |
| `checkpoints` | `models/checkpoints` | All-in-one checkpoint files such as `.safetensors`, `.ckpt`, `.pt`, `.pth`, `.bin`, `.pkl`, `.sft`. |
| `configs` | `models/configs` | YAML configs used by some checkpoint loaders. |
| `loras` | `models/loras` | LoRA, LoCon, LoHA, and compatible adapter files. |
| `vae` | `models/vae` | VAE files; VAE precision can be controlled by CLI flags. |
| `text_encoders` | `models/text_encoders`, `models/clip` | Standalone CLIP/T5/text encoders; legacy `clip` maps to this category. |
| `diffusion_models` | `models/unet`, `models/diffusion_models` | Standalone diffusion/UNet model files; legacy `unet` maps to this category. |
| `controlnet` | `models/controlnet`, `models/t2i_adapter` | ControlNet and T2I-Adapter files. |
| `clip_vision` | `models/clip_vision` | CLIP vision encoders. |
| `upscale_models` | `models/upscale_models` | ESRGAN, RealESRGAN, SwinIR, Swin2SR, and similar upscalers. |
| `embeddings` | `models/embeddings` | Textual inversion embeddings. |
| `diffusers` | `models/diffusers` | Folder-based Diffusers layouts. |
| `vae_approx` | `models/vae_approx` | TAESD/preview helper models. |
| `style_models`, `gligen`, `hypernetworks`, `photomaker`, `model_patches` | matching `models/<category>` folders | Specialized model types consumed by dedicated nodes. |
| `audio_encoders`, `classifiers`, `background_removal`, `frame_interpolation`, `geometry_estimation`, `optical_flow`, `detection` | matching `models/<category>` folders | Auxiliary categories for audio, vision, video, and detection workflows. |
| `custom_nodes` | `custom_nodes` | Extension folders, not model weights; route implementation work to `../../custom-nodes/SKILL.md`. |

The `--base-directory` flag resets the base for `models`, `custom_nodes`, `input`, `output`, `temp`, and `user`. Separate `--input-directory`, `--output-directory`, `--temp-directory`, and `--user-directory` flags can override those specific paths.

## Extra Config Loading

ComfyUI loads `extra_model_paths.yaml` from the application directory when present. It also accepts one or more explicit configs through `--extra-model-paths-config PATH`.

An extra config has this shape:

```yaml
profile-name:
  base_path: shared-models
  is_default: true
  checkpoints: checkpoints
  loras: |
    loras
    other-loras
  vae: vae
```

Top-level keys are arbitrary profile names. Each profile may contain:

- `base_path`: optional root for that profile; environment variables and `~` are expanded by ComfyUI.
- `is_default`: optional boolean-like value; when true, paths are placed before existing paths in their category.
- model categories: each value is a string split on newlines. Blank lines are ignored.

Resolution rules:

- If `base_path` is present and a category entry is relative, the resolved path is `base_path/category-entry`.
- If `base_path` is absent and a category entry is relative, the resolved path is relative to the YAML file location.
- Absolute category entries stay absolute.
- Duplicate category paths are not added twice; if re-added with `is_default`, they move to the front.
- Legacy category names are mapped: `clip` becomes `text_encoders`, and `unet` becomes `diffusion_models`.

## Good Config Examples

Shared ComfyUI-style model root:

```yaml
shared:
  base_path: shared-comfy
  checkpoints: models/checkpoints
  configs: models/configs
  loras: models/loras
  vae: models/vae
  text_encoders: |
    models/text_encoders
    models/clip
  diffusion_models: |
    models/unet
    models/diffusion_models
```

Automatic1111-style root:

```yaml
a1111:
  base_path: stable-diffusion-webui
  checkpoints: models/Stable-diffusion
  configs: models/Stable-diffusion
  vae: models/VAE
  loras: |
    models/Lora
    models/LyCORIS
  embeddings: embeddings
  controlnet: models/ControlNet
```

Config next to a project-specific model directory:

```yaml
project:
  checkpoints: ../models/checkpoints
  loras: ../models/loras
```

## Validation Workflow

Run:

```bash
python ../scripts/validate_extra_model_paths.py extra_model_paths.yaml --strict
```

Interpret results:

- YAML parse error: fix indentation, tabs, quoting, or block scalar syntax first.
- Unknown category: check spelling or decide whether a custom node intentionally registers that category at runtime.
- Missing `base_path`: create/mount the root or correct the path.
- Missing category path: create/mount that model folder or remove the stale entry.
- Duplicate path: harmless but confusing; keep one entry unless `is_default` ordering is intentional.

## Loader Node Name Mismatches

If a graph references a filename that is not visible in a loader dropdown:

1. Identify the loader node type and expected category; graph JSON details belong to `../../workflow-execution/SKILL.md`.
2. Place the file under the matching category, not just any `models/` subfolder.
3. Refresh ComfyUI or restart after editing extra paths.
4. Confirm extension support. Most weight categories accept checkpoint-like extensions; `configs` expects YAML, and `diffusers` expects folders.
5. For split-model workflows, ensure all referenced pieces exist: diffusion model, text encoder(s), VAE, LoRA, ControlNet, and any vision/audio helper models.
