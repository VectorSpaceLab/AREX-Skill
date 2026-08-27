# API Reference

## Verified model constructors

The following signatures were inspected from the repo source and a live CPU environment.

### `models.build.build_model(config, is_pretrain=False)`

Dispatches on `config.MODEL.TYPE`:

- `swin` -> `SwinTransformer`
- `swinv2` -> `SwinTransformerV2`
- `swin_moe` -> `SwinTransformerMoE`
- `swin_mlp` -> `SwinMLP`
- `is_pretrain=True` -> `build_simmim(config)`

### `SwinTransformer`

```text
SwinTransformer(img_size=224, patch_size=4, in_chans=3, num_classes=1000,
                embed_dim=96, depths=[2, 2, 6, 2], num_heads=[3, 6, 12, 24],
                window_size=7, mlp_ratio=4.0, qkv_bias=True, qk_scale=None,
                drop_rate=0.0, attn_drop_rate=0.0, drop_path_rate=0.1,
                norm_layer=torch.nn.LayerNorm, ape=False, patch_norm=True,
                use_checkpoint=False, fused_window_process=False, **kwargs)
```

### `SwinTransformerV2`

```text
SwinTransformerV2(img_size=224, patch_size=4, in_chans=3, num_classes=1000,
                  embed_dim=96, depths=[2, 2, 6, 2], num_heads=[3, 6, 12, 24],
                  window_size=7, mlp_ratio=4.0, qkv_bias=True, drop_rate=0.0,
                  attn_drop_rate=0.0, drop_path_rate=0.1,
                  norm_layer=torch.nn.LayerNorm, ape=False, patch_norm=True,
                  use_checkpoint=False, pretrained_window_sizes=[0, 0, 0, 0], **kwargs)
```

### `SwinMLP`

```text
SwinMLP(img_size=224, patch_size=4, in_chans=3, num_classes=1000,
        embed_dim=96, depths=[2, 2, 6, 2], num_heads=[3, 6, 12, 24],
        window_size=7, mlp_ratio=4.0, drop_rate=0.0, drop_path_rate=0.1,
        norm_layer=torch.nn.LayerNorm, ape=False, patch_norm=True,
        use_checkpoint=False, **kwargs)
```

### SimMIM encoder wrapper

The SimMIM wrapper in `models/simmim.py` is constructed as:

```text
SimMIM(config, encoder, encoder_stride, in_chans, patch_size)
```

The internal encoder class is `SwinTransformerForSimMIM` or `SwinTransformerV2ForSimMIM` depending on `MODEL.TYPE`.

## Important verified behavior

- `SwinTransformer` uses a standard relative position bias table.
- `SwinTransformerV2` uses continuous relative position bias and `pretrained_window_sizes`.
- `SwinMLP` swaps attention for a grouped spatial MLP inside windows.
- All three model families can be instantiated on CPU for shape/sanity checks.
- The optional fused window-process import is guarded; missing the extension prints a warning and falls back.
- MoE imports are guarded by `tutel`; missing Tutel does not block the baseline model families.

## Shape and config constraints

- `DATA.IMG_SIZE` must be divisible by the patch geometry used by the model family and by SimMIM mask settings when the model is used for masked pretraining.
- The window size should be chosen so the feature map resolution after patch embedding can be partitioned cleanly.
- When shrinking a config for a smoke test, keep the stage depths and head counts aligned with the model family rather than mixing V1 and V2 assumptions.

## Minimal inspection recipe

1. Load a config with `scripts/inspect_swin_config.py`.
2. Use `scripts/smoke_model_build.py` to build a tiny CPU model.
3. Confirm the output shape is `[batch, num_classes]` for classifier models or a reconstruction tensor for SimMIM smoke checks.
