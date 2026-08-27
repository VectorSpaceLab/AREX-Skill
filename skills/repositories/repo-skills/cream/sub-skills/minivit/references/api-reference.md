# MiniViT API Reference

## Mini-DeiT constructors

Mini-DeiT registers these model names through timm after the Mini-DeiT model module is imported:

| Name | Underlying DeiT size | Input | Verified/important settings |
| --- | --- | --- | --- |
| `mini_deit_tiny_patch16_224` | Tiny, embed dim 192 | 224 | `repeated_times=2`, `use_transform=True`, `use_cls_token=False`; CPU instantiation verified. |
| `mini_deit_small_patch16_224` | Small, embed dim 384 | 224 | Same MiniViT/iRPE settings. |
| `mini_deit_base_patch16_224` | Base, embed dim 768 | 224 | Same MiniViT/iRPE settings. |
| `mini_deit_base_patch16_384` | Base, embed dim 768 | 384 | Higher-resolution model; use `--input-size 384` for commands. |

The inspected `mini_deit_tiny_patch16_224` model exposes `head.weight` with shape `(1000, 192)`, matching ImageNet-1k classification over a 192-dimensional tiny embedding.

## Mini-DeiT iRPE settings

`get_deit_rpe_config()` calls the iRPE config builder with:

```text
ratio=1.9, method='product', mode='ctx', shared_head=True, skip=0, rpe_on='k'
```

This applies image relative-position encoding on keys. If `rpe_ops` is unavailable, import emits a warning and uses the Python fallback.

## Mini-Swin config and builder surface

Mini-Swin uses a YACS config. Important keys:

| Config area | Keys to inspect |
| --- | --- |
| Data | `DATA.DATA_PATH`, `DATA.BATCH_SIZE`, `DATA.IMG_SIZE`, `DATA.LOAD_TAR`, `DATA.ZIP_MODE` |
| Model | `MODEL.TYPE`, `MODEL.NAME`, `MODEL.RESUME`, `MODEL.DROP_PATH_RATE`, `MODEL.SWIN.*` |
| Distillation | `DISTILL.DO_DISTILL`, `DISTILL.TEACHER`, `DISTILL.STUDENT_LAYER_LIST`, `DISTILL.TEACHER_LAYER_LIST`, `DISTILL.ATTN_LOSS`, `DISTILL.HIDDEN_LOSS`, `DISTILL.HIDDEN_RELATION`, `DISTILL.RESUME_WEIGHT_ONLY` |
| MiniViT transforms | `MINIVIT.IS_SEP_LAYERNORM`, `MINIVIT.IS_TRANSFORM_FFN`, `MINIVIT.IS_TRANSFORM_HEADS`, `MINIVIT.SEPARATE_LAYERNUM_LIST` |
| 384 finetune | `TRAIN.TRAIN_224TO384`, `DATA.IMG_SIZE`, `TRAIN.EPOCHS`, `TRAIN.BASE_LR` |

`MODEL.TYPE` routing:

| `MODEL.TYPE` | Builder result |
| --- | --- |
| `swin` | Standard Swin transformer. |
| `swin_minivit` | MiniViT Swin without distillation outputs. |
| `swin_minivit_distill` | MiniViT Swin with distillation output taps; used by documented Mini-Swin configs. |
| `swin_mlp` | Swin-MLP branch; not a MiniViT target. |

## Safe inspection notes

- Mini-DeiT parser help and tiny CPU instantiation are safe in the prepared inspection environment.
- Mini-Swin config parsing with a real `--cfg` is safe. Full Mini-Swin `main.py` execution initializes CUDA/distributed state and should not be used as a cheap smoke test.
- Mini-Swin imports Apex optionally, but non-`O0` AMP asserts Apex is available during execution.
