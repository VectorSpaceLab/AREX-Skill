# Dense-to-NaFlex Conversion and Checkpoint Notes

## When Conversion Applies

Use conversion guidance when the user wants a dense OpenCLIP/timm vision tower to consume NaFlex patch dictionaries or wants to load dense checkpoints into a NaFlex-compatible vision tower.

Two separate knobs matter:

- `--force-naflex-vision`: converts a compatible image vision tower to a timm `NaFlexVit`-style tower without enabling NaFlex dataloaders.
- `--use-naflex`: enables NaFlex data and eval loaders; for ordinary image models it also implies `force_naflex_vision`.

Do not apply image-tower conversion to GenLIP, GenLAP, or NaFlexCLAP:

- GenLIP has its own GenLIP image patch embedding/trunk.
- GenLAP uses an audio spectrogram prefix, not an image tower.
- NaFlexCLAP uses a NaFlex spectrogram-ViT audio tower and contrastive CLAP wiring.

## Compatible Vision Towers

`apply_naflex_vision_config(model_cfg)` chooses a path from `model_cfg["vision_cfg"]`:

- If `vision_cfg.timm_model_name` exists, conversion uses timm mode.
- If no timm model name exists, conversion attempts native OpenCLIP/OpenAI ViT mode.

Supported timm mode:

- Explicit timm names starting with `naflexvit` are already native NaFlex and are accepted directly.
- Compatible timm EVA/ViT-family models can be converted by adding `use_naflex=True` to `timm_model_kwargs`.
- Unsupported timm models raise an error asking for a timm EVA/ViT model or explicit `naflexvit` config.

Supported native OpenCLIP ViT mode requires a standard ViT-like config:

- No timm model name and not a ResNet/tuple-layer tower.
- Token pooling (`pool_type="tok"`) with no attentional pool.
- Standard pre/post norm settings: no `no_ln_pre`, no `final_ln_after_pool`.
- No output tokens and learnable absolute position embeddings.
- No unsupported custom block knobs such as qk norm, scaled cosine attention, head/attention/fc scaling, custom act/norm kwargs, or non-default block type.
- Width must divide evenly by `head_width` to compute attention heads.

Unsupported native towers raise a runtime error explaining NaFlex can only convert standard native OpenCLIP/OpenAI ViT towers or compatible timm EVA/ViT towers.

## Native ViT Config Rewrite

For standard native ViT towers, conversion rewrites the vision config into a timm `vit_base_patch16_clip_224` NaFlex-style trunk with:

- `timm_model_kwargs.use_naflex=True`.
- Linear patch embedding over pre-patchified input.
- Learned position embedding grid from the original dense image/patch size.
- Token global pooling and class token behavior matching the native ViT path.
- QuickGELU activation when the original model config had `quick_gelu=True`.

The conversion preserves intended dense outputs when weights are converted and loaded into the NaFlex tower, according to tests that compare native dense image features with converted NaFlex dense-image features.

## Checkpoint State-Dict Conversion

`convert_naflex_state_dict(model, state_dict)` delegates to timm/native conversion only when the model's `visual.trunk` is a `NaFlexVit`.

Native OpenCLIP ViT checkpoints:

- `visual.class_embedding` is folded with the first positional embedding into `visual.trunk.embeds.cls_token`.
- Patch positional embeddings are reshaped from flattened square grid tokens to `visual.trunk.embeds.pos_embed` with shape `(1, grid_h, grid_w, dim)`.
- Conv patch embed weights are permuted and flattened into linear patch-projection weights.
- Transformer block keys are mapped from OpenCLIP names to timm-like `blocks.*` names.
- Text-side weights are preserved unchanged.
- Non-square native positional grids are rejected because the converter infers `grid_size = sqrt(num_patch_tokens)`.

Timm checkpoints:

- Existing NaFlex/timm keys under `visual.trunk.*` are filtered through timm's `checkpoint_filter_fn` when available.
- Dense conv patch-projection weights map to linear `embeds.proj.weight` for NaFlexVit.
- If timm lacks `naflexvit` support, conversion may become a no-op and model loading will surface missing/unexpected keys.

## Practical Decision Tree

1. If the user has a standard dense CLIP inference task, route to dense model inference instead of forcing NaFlex.
2. If they need variable-resolution/aspect training or eval, use `--use-naflex` and ensure `aug_cfg use_timm=True naflex=True`.
3. If they only need to test converted model construction or load dense weights into a NaFlex tower, use `force_naflex_vision=True` / `--force-naflex-vision` without enabling NaFlex data.
4. If the model is ResNet, non-standard ViT, or custom attention/pooling, do not promise conversion; expect a runtime rejection.
5. If the checkpoint has dense native ViT weights, run the model factory load path or `convert_naflex_state_dict` so positional/class/patch weights are remapped.
6. If the checkpoint architecture is GenLIP/GenLAP, do not use the dense CLIP conversion path; match the exact generative config.

## Minimal Python Pattern

```python
import open_clip

model = open_clip.create_model(
    "ViT-B-16",
    pretrained=None,
    force_naflex_vision=True,
)
```

For eval transforms with patch dictionaries:

```python
model, _, preprocess_val = open_clip.create_model_and_transforms(
    "naflex_ViT-B-16",
    pretrained=None,
    aug_cfg={"use_timm": True, "naflex": True},
)
```

Keep the two steps conceptually separate: model conversion controls the tower; NaFlex aug/data config controls emitted patch dictionaries.

## Common Conversion Mistakes

- Using `--force-naflex-vision` alone and expecting dataloaders to emit patch dictionaries. It does not enable the data pipeline.
- Using `--use-naflex` on GenLIP and then expecting `force_naflex_vision=True`. GenLIP intentionally disables image-tower conversion because its architecture is already generative/NaFlex-specific.
- Loading a dense checkpoint with an incompatible non-square positional grid or unsupported custom ViT options and expecting automatic remapping.
- Assuming NaFlexCLAP is image NaFlex. It is an audio spectrogram-ViT CLAP route.
