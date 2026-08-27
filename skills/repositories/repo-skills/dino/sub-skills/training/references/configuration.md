# DINO training configuration

DINO loads a Python config with `SLConfig.fromfile`, recursively merges its
`_base_` files, then merges `--options` before attaching config values to the
argument namespace. Config files are code, not inert data: inspect a trusted
file before using it. The shipped configs inherit augmentation values from
`coco_transformer.py`.

## Shipped configurations

| Config | Backbone | Returned backbone indices | Feature levels | Per-process batch |
|---|---|---:|---:|---:|
| `DINO_4scale.py` | `resnet50` | `[1, 2, 3]` | 4 | 2 |
| `DINO_5scale.py` | `resnet50` | `[0, 1, 2, 3]` | 5 | 1 |
| `DINO_4scale_swin.py` | `swin_L_384_22k` | `[1, 2, 3]` | 4 | 2 |
| `DINO_4scale_convnext.py` | `convnext_xlarge_22k` | `[1, 2, 3]` | 4 | 2 |

A four-scale model returns three backbone outputs and adds one projected
feature level. A five-scale ResNet model returns four backbone outputs and
adds one projected level. Keep `return_interm_indices` and
`num_feature_levels` paired: the DINO backbone builder accepts only
`[0, 1, 2, 3]`, `[1, 2, 3]`, or `[3]`, and this route's shipped 4/5-scale
choices use the first two respectively.

The repository's accepted backbone names are `resnet50`, `resnet101`,
`swin_T_224_1k`, `swin_B_224_22k`, `swin_B_384_22k`, `swin_L_224_22k`,
`swin_L_384_22k`, and `convnext_xlarge_22k`. The shipped run recipes cover
ResNet-50, Swin-L 384, and ConvNeXt-XL. Swin and ConvNeXt initialization
requires a local pretrained asset directory; the Swin builder selects a
backbone-specific filename from it and ConvNeXt receives it as `backbone_dir`.
Do not assume a ResNet config can consume a Swin or ConvNeXt checkpoint.

## Important model and training options

| Option | Role and safe interpretation |
|---|---|
| `modelname` | Must be `dino` for this route. |
| `backbone`, `return_interm_indices`, `num_feature_levels` | Select the backbone feature hierarchy and four/five-scale transformer inputs. |
| `hidden_dim=256`, `nheads=8`, `enc_layers=6`, `dec_layers=6` | Transformer shape choices. Changing them invalidates many checkpoints. |
| `num_queries=900` | Number of object queries. It affects memory and checkpoint shape. |
| `enc_n_points=4`, `dec_n_points=4` | Deformable-attention sampling points. The CUDA extension must support the selected model. |
| `lr=1e-4`, `lr_backbone=1e-5` | With `param_dict_type=default`, non-backbone parameters use `lr` and backbone parameters use `lr_backbone`. `lr_backbone` must stay positive because the builder requires a trainable backbone. |
| `param_dict_type` | `default`, `ddetr_in_mmdet`, or `large_wd`; inspect `util/get_param_dicts.py` before changing parameter groups. |
| `batch_size` | BatchSampler size **per process**. Multiply by the distributed world size for the global batch. |
| `epochs`, `lr_drop`, `save_checkpoint_interval` | Epoch count, StepLR boundary, and periodic full-checkpoint interval. Defaults are 12, 11, and 1. |
| `onecyclelr`, `multi_step_lr`, `lr_drop_list` | Select the scheduler branch. `onecyclelr` steps every training batch; `multi_step_lr` uses the list of milestones; otherwise StepLR uses `lr_drop`. |
| `clip_max_norm=0.1` | Gradient clipping threshold; zero disables clipping. |
| `use_dn`, `dn_number`, `dn_box_noise_scale`, `dn_label_noise_ratio` | Query-de-noising behavior. The model uses `dn_number` when `use_dn` is true; do not substitute the unused legacy `dn_scalar` launcher key. |
| `dn_labelbook_size` | Label embedding capacity used by denoising. Apply the custom-data rule below. |
| `aux_loss`, `masks`, loss coefficients | Auxiliary decoder losses and optional segmentation. Mask training needs its own data/model setup and is not the ordinary detection route. |
| `use_ema`, `ema_decay`, `ema_epoch` | Optional EMA model and best-EMA checkpoints. |
| `data_aug_scales`, `data_aug_max_size`, `data_aug_scales2_resize`, `data_aug_scales2_crop` | Multi-scale and crop augmentation inherited from `coco_transformer.py`; changing them changes the experiment and memory use. |

The optimizer is AdamW. `util/get_param_dicts.py` creates parameter groups
based on the selected `param_dict_type`; there is no automatic learning-rate
scaling from the global batch size.

## Config overrides and parser arguments

The parser accepts a repeatable-looking group in one invocation:

```bash
python main.py -c config/DINO/DINO_4scale.py \
  --output_dir runs/override --coco_path /data/COCO \
  --options batch_size=1 epochs=2 use_ema=False
```

`DictAction` splits each token at the first `=`, parses integers, floats,
`true`/`false`, `none`/`null`, and comma-separated lists. Use `True`/`False`
for readability and no spaces around `=`. Put the group last because
`nargs='+'` consumes all subsequent non-option tokens.

Use the direct parser flags for `--config_file`/`-c`, `--coco_path`,
`--dataset_file`, `--output_dir`, `--resume`, `--pretrain_model_path`,
`--finetune_ignore`, `--device`, `--num_workers`, `--seed`, and `--amp`.
Do not put those names inside `--options`: after merging, `main.py` raises
`ValueError` when a config key collides with an existing parser argument.
Unknown keys may be accepted by `SLConfig` but fail later when a model,
dataset, or scheduler accesses a missing attribute. The bundled planner
rejects unknown keys unless `--allow-unknown-option` is explicit.

The shell launchers in this checkout append `dn_scalar=100`,
`dn_label_coef=1.0`, and `dn_bbox_coef=1.0`. They are accepted as arbitrary
config attributes but are not read by the current model/config sources. Use
the current names in the table above and do not infer behavior from those
legacy tokens.

## Custom COCO-style class configuration

This route assumes the custom data has already been made compatible with the
repository's COCO dataset loader. Layout and annotation validation belong to
[data-model-setup](../../data-model-setup/SKILL.md); this section only defines
the model's class-count contract.

`models/dino/dino.py` documents `num_classes` as `max_obj_id + 1`. For
category IDs `1..K`, set `num_classes=K+1`. For a one-class dataset using
category ID 1, set `num_classes=2`. If IDs are sparse, use the maximum actual
category ID plus one and ensure the annotation labels are intentional; using
the count of names alone can make the classifier and denoising labels
incompatible.

The README's custom-training instructions state the conservative rule:

```text
dn_labelbook_size >= num_classes + 1
```

For example, with category IDs `1..4`, use `num_classes=5` and at least
`dn_labelbook_size=6` when following that rule. The shipped COCO reference
configs set both values to 91, so do not mechanically reject a stock COCO
config; for custom data make the conservative value explicit. The model
constructs a label embedding of size `dn_labelbook_size + 1`, and denoising
labels are taken from the dataset, so a too-small labelbook can fail during
training even if the classifier head appears to load.

A safe custom fine-tuning shape is:

```bash
python main.py \
  --output_dir runs/custom-ms4 \
  -c config/DINO/DINO_4scale.py --coco_path /data/custom-coco \
  --pretrain_model_path /data/checkpoints/dino-r50.pth \
  --finetune_ignore label_enc.weight class_embed \
  --options num_classes=5 dn_labelbook_size=6
```

Use a new output directory. A pre-existing rolling `checkpoint.pth` changes
this into a full resume and prevents the pretrain branch from running.
Inspect the logged missing/unexpected keys after the non-strict load.

## Checkpoint compatibility dimensions

Before using `--resume`, match at least:

- config scale and `num_feature_levels`;
- backbone and returned feature indices;
- `hidden_dim`, query count, decoder dimensions, and denoising embedding;
- `num_classes`, `dn_labelbook_size`, and class-head shape; and
- model options that alter module names or tensor shapes.

A full resume calls strict model loading. A partial pretrain load is more
forgiving but is not proof that the new model was initialized as intended.
Record the exact checkpoint/config pair and the load result in the handoff.
