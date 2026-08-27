# D-FINE API Reference

## Purpose

Read this when you need verified D-FINE API names, signatures, registry behavior, or model construction facts. The entries below are distilled from the D-FINE source modules and live import/model-construction inspection.

## Config and registry lifecycle

D-FINE uses a registry-centered YAML system:

1. Importing `src` imports `data`, `nn`, `optim`, and `zoo` for registration side effects.
2. Classes decorated with `@register()` are recorded in `GLOBAL_CONFIG` under their class name unless an explicit name is supplied.
3. `YAMLConfig(cfg_path: str, **kwargs)` loads YAML includes, merges command-line overrides, and exposes lazy properties such as `model`, `criterion`, `postprocessor`, `optimizer`, dataloaders, `ema`, and `scaler`.
4. `create(type_or_name, global_cfg=GLOBAL_CONFIG, **kwargs)` resolves YAML entries. If a config entry is a dictionary with `type`, D-FINE first loads the registered schema for that type, then merges YAML values and injected/shared dependencies.
5. `__inject__` lists fields that should be recursively constructed from other config entries. `__share__` lists fields taken from global config when present.

Common registry errors usually mean the module defining the class was never imported, the YAML `type` string is misspelled, or an injected field names a missing config block.

## Verified core signatures

| Object | Signature / role |
|---|---|
| `src.core.YAMLConfig` | `YAMLConfig(cfg_path: str, **kwargs) -> None`; loads included YAML and merges overrides. |
| `src.core.register` | `register(dct=GLOBAL_CONFIG, name=None, force=False)`; decorator for class/function registration. |
| `src.core.create` | `create(type_or_name, global_cfg=GLOBAL_CONFIG, **kwargs)`; builds registered objects from strings or types. |
| `src.zoo.dfine.dfine.DFINE` | `DFINE(backbone: nn.Module, encoder: nn.Module, decoder: nn.Module)`; forward is backbone -> encoder -> decoder. |
| `src.nn.backbone.hgnetv2.HGNetv2` | `HGNetv2(name, use_lab=False, return_idx=[1, 2, 3], freeze_stem_only=True, freeze_at=0, freeze_norm=True, pretrained=True, local_model_dir='weight/hgnetv2/')`. |
| `src.zoo.dfine.hybrid_encoder.HybridEncoder` | `HybridEncoder(in_channels=[512,1024,2048], feat_strides=[8,16,32], hidden_dim=256, nhead=8, dim_feedforward=1024, dropout=0.0, enc_act='gelu', use_encoder_idx=[2], num_encoder_layers=1, pe_temperature=10000, expansion=1.0, depth_mult=1.0, act='silu', eval_spatial_size=None)`. |
| `src.zoo.dfine.dfine_decoder.DFINETransformer` | `DFINETransformer(num_classes=80, hidden_dim=256, num_queries=300, feat_channels=[512,1024,2048], feat_strides=[8,16,32], num_levels=3, num_points=4, nhead=8, num_layers=6, dim_feedforward=1024, dropout=0.0, activation='relu', num_denoising=100, label_noise_ratio=0.5, box_noise_scale=1.0, learn_query_content=False, eval_spatial_size=None, eval_idx=-1, eps=0.01, aux_loss=True, cross_attn_method='default', query_select_method='default', reg_max=32, reg_scale=4.0, layer_scale=1)`. |
| `src.zoo.dfine.dfine_criterion.DFINECriterion` | `DFINECriterion(matcher, weight_dict, losses, alpha=0.2, gamma=2.0, num_classes=80, reg_max=32, boxes_weight_format=None, share_matched_indices=False)`. |
| `src.zoo.dfine.matcher.HungarianMatcher` | `HungarianMatcher(weight_dict, use_focal_loss=False, alpha=0.25, gamma=2.0)`. |
| `src.zoo.dfine.postprocessor.DFINEPostProcessor` | `DFINEPostProcessor(num_classes=80, use_focal_loss=True, num_top_queries=300, remap_mscoco_category=False)`. |
| `src.data.dataset.coco_dataset.CocoDetection` | `CocoDetection(img_folder, ann_file, transforms, return_masks=False, remap_mscoco_category=False)`. |
| `src.data.dataloader.BatchImageCollateFunction` | `BatchImageCollateFunction(stop_epoch=None, ema_restart_decay=0.9999, base_size=640, base_size_repeat=None)`. |

## Lazy property gotchas

- `YAMLConfig(...).yaml_cfg` is a plain merged dictionary and is safe to inspect.
- `cfg.model`, `cfg.criterion`, and `cfg.postprocessor` instantiate modules lazily. This can trigger pretrained backbone lookup unless `HGNetv2.pretrained` is disabled or valid weights exist.
- `cfg.train_dataloader`, `cfg.val_dataloader`, and `cfg.evaluator` may open datasets and annotations. Avoid them in simple architecture inspection unless dataset paths are valid.
- `cfg.optimizer` builds model parameters first and applies regex groups from the optimizer config.

## Model construction smoke fact

A verified inspection built the smallest COCO config with `HGNetv2.pretrained=False`: `configs/dfine/dfine_hgnetv2_n_coco.yml` produced a `DFINE` model with 3,782,693 parameters and a `DFINEPostProcessor`. Use this as a sanity pattern, not as a benchmark claim.

## Adding a registered component

1. Implement the class with the same constructor fields you want to expose in YAML.
2. Decorate it with `@register()` from `src.core`.
3. Ensure the module is imported by an already imported package initializer or by the code path that loads configs.
4. If it depends on another registered object, set `__inject__ = ['field_name']`; if it needs global fields like `num_classes`, set `__share__ = ['num_classes']`.
5. In YAML, set `type: NewClassName` where an inline object is expected, or assign a top-level block and reference it from an injected field.
6. Probe with `scripts/inspect_dfine_model.py --build-model` before running training.

## Safe inspection pattern

```bash
python ../scripts/inspect_dfine_model.py \
  --repo-root <d-fine-checkout> \
  --config configs/dfine/dfine_hgnetv2_n_coco.yml \
  --build-model
```

The helper disables HGNetv2 pretrained lookup by default so import/model construction does not require network access or local backbone weights.
