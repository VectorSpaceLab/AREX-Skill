# D-FINE Model Architecture Notes

## Purpose

Read this for operational guidance on D-FINE's model graph, config knobs, model-size families, deploy mode, and architecture-level changes. This is not a paper summary; it focuses on what future agents need to inspect, debug, or adapt the repository.

## Component graph

The canonical D-FINE detection config declares:

```yaml
task: detection
model: DFINE
criterion: DFINECriterion
postprocessor: DFINEPostProcessor
DFINE:
  backbone: HGNetv2
  encoder: HybridEncoder
  decoder: DFINETransformer
```

Runtime assembly is:

```text
input image tensor
  -> HGNetv2 backbone features
  -> HybridEncoder multi-scale features
  -> DFINETransformer decoder outputs
  -> DFINECriterion during training OR DFINEPostProcessor during evaluation/export
```

`DFINE.deploy()` switches the model to eval mode and calls `convert_to_deploy()` on child modules that implement it. Export/inference wrappers typically use `cfg.model.deploy()` together with `cfg.postprocessor.deploy()`.

## Model-size families

D-FINE uses model size letters in config names:

| Size | Typical config pattern | Main knobs changed |
|---|---|---|
| `n` | `dfine_hgnetv2_n_*` | HGNetv2 `B0`, two feature levels, smaller hidden dims/layers, fewer FLOPs. |
| `s` | `dfine_hgnetv2_s_*` | Small HGNetv2 model with moderate encoder/decoder width. |
| `m` | `dfine_hgnetv2_m_*` | Medium width/depth and larger compute. |
| `l` | `dfine_hgnetv2_l_*` | Large default family used in many README examples. |
| `x` | `dfine_hgnetv2_x_*` | Largest released family; highest compute and checkpoint size. |

Dataset suffixes identify the training/evaluation target: `coco`, `obj365`, `obj2coco`, `custom`, `obj2custom`, or CrowdHuman/VOC variants.

## D-FINE-specific knobs

Important decoder and loss fields from `configs/dfine/include/dfine_hgnetv2.yml`:

- `eval_spatial_size`: exported/evaluation spatial size, commonly `[640, 640]`.
- `DFINETransformer.num_queries`: object queries, default `300`.
- `DFINETransformer.num_layers`: decoder layers, default `6` in the include file.
- `DFINETransformer.num_points`: multi-scale deformable attention sampling points.
- `DFINETransformer.reg_max`: distribution bins for fine-grained localization, default `32`.
- `DFINETransformer.reg_scale`: distribution scale, default `4`.
- `DFINETransformer.cross_attn_method`: `default` or `discrete` depending on model config.
- `DFINETransformer.query_select_method`: `default` or alternative selection strategy.
- `DFINECriterion.weight_dict`: loss weights including `loss_vfl`, `loss_bbox`, `loss_giou`, `loss_fgl`, and `loss_ddf`.

Changing these fields may require matching checkpoint weights, postprocessor expectations, and training schedule changes. Treat architecture and checkpoint compatibility as coupled.

## Input-size changes

When a task changes input size, coordinate at least these surfaces:

1. Dataset transforms: resize operations in the train and validation dataloaders.
2. Collate function: `BatchImageCollateFunction.base_size` and `base_size_repeat` when multiscale batching is used.
3. Architecture/export: `eval_spatial_size` in the model include.
4. Training schedule/resource planning: smaller input may permit larger batch size; larger input may need smaller batch size or more GPUs.
5. Export/inference preprocessing: native inference scripts generally assume `640` unless adapted.

Route dataset config edits to `data-and-configs`; route launch changes to `training-evaluation`; route backend export/inference changes to `inference-export`.

## Checkpoint compatibility surfaces

Checkpoint loading can fail or partially load when:

- `num_classes` differs from the checkpoint head.
- A `custom` or Objects365-to-COCO/custom flow changes class mappings.
- `reg_max`, hidden dim, feature channels, feature levels, or decoder layer counts differ.
- A pretrained checkpoint stores EMA weights under `ema.module`, while a simplified checkpoint stores `model`.
- A model was saved under DDP with `module.` prefixes.

The solver includes matching and class-head adjustment logic for tuning. For deployment/export, use the inference/export EMA extractor when a simpler `{model: ...}` checkpoint is needed.

## When a forward smoke is appropriate

A dummy forward is useful only after config/model construction succeeds. It may be slow on CPU and can consume substantial memory for `640x640` inputs, so make it explicit:

```bash
python ../scripts/inspect_dfine_model.py \
  --repo-root <d-fine-checkout> \
  --config configs/dfine/dfine_hgnetv2_n_coco.yml \
  --build-model \
  --dummy-forward \
  --dummy-size 320
```

If the goal is only to prove registry/config health, omit `--dummy-forward`.

## Editing decision checklist

Before changing architecture code or YAML:

- Which registered class name will the YAML use?
- Does the class need `__inject__` dependencies?
- Does it need global shared values such as `num_classes` or `eval_spatial_size`?
- Are feature channel counts and strides consistent across backbone, encoder, and decoder?
- Does a checkpoint need head or shape adjustment?
- Can `scripts/inspect_dfine_model.py --build-model` still build the smallest intended config?
- Are training and export/inference references updated for the changed config surface?
