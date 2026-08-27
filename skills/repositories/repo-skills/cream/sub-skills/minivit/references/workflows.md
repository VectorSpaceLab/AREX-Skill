# MiniViT Workflows

## Scope

This reference covers two MiniViT branches:

- **Mini-DeiT**: DeiT-style ImageNet models with iRPE on keys, no class token, two-way weight multiplexing, and optional teacher distillation.
- **Mini-Swin**: Swin-style ImageNet models with MiniViT shared-block transformations, optional attention/hidden-state distillation, and a Base 224-to-384 finetune path.

For generic relative-position-encoding integration use the `irpe` sub-skill. For TinyViT or EfficientViT use their own sub-skills.

## Mini-DeiT workflow

### 1. Select the variant

| Variant key | Model argument | Input | Notes |
| --- | --- | --- | --- |
| `tiny` | `mini_deit_tiny_patch16_224` | 224 | Smallest Mini-DeiT; safe CPU instantiation target. |
| `small` | `mini_deit_small_patch16_224` | 224 | Mid-size Mini-DeiT. |
| `base` | `mini_deit_base_patch16_224` | 224 | Base Mini-DeiT; documented drop-path `0.1`. |
| `base-384` | `mini_deit_base_patch16_384` | 384 | Higher-resolution finetune/eval path; use `--input-size 384`. |

Mini-DeiT constructors register through timm. The inspected tiny variant builds on CPU and exposes an ImageNet classifier head shaped `1000 x 192`.

### 2. Validate data

Mini-DeiT accepts ImageNet folder splits:

```text
ImageNet/
├── train/
└── val/
```

or tar archives:

```text
ImageNet/
├── train.tar
└── val.tar
```

Check the layout first:

```bash
python ../../../scripts/check_dataset_layout.py --root /path/to/ImageNet --kind imagenet1k
```

Use `--load-tar` only for `train.tar` / `val.tar` layouts.

### 3. Train/evaluate

Mini-DeiT training usually uses soft distillation with a RegNetY teacher:

- `--teacher-model regnety_160`
- `--distillation-type soft`
- `--distillation-alpha 1.0`
- optional `--teacher-path /path/to/teacher_checkpoint.pth`

If `--teacher-path` is omitted, the script may try to use a pretrained timm/torch-hub teacher. Provide a local teacher checkpoint when downloads are not acceptable.

Evaluation uses `--resume /path/to/mini_deit_checkpoint.pth --eval`. The Base-384 path also uses `--input-size 384`.

## Mini-Swin workflow

### 1. Select the variant/config

| Variant key | YAML config | Documented checkpoint family |
| --- | --- | --- |
| `tiny` | `configs/swin_tiny_patch4_window7_224_minivit_sharenum6.yaml` | `mini-swin-tiny-12m.pth` |
| `small` | `configs/swin_small_patch4_window7_224_minivit_sharenum2.yaml` | `mini-swin-small-26m.pth` |
| `base` | `configs/swin_base_patch4_window7_224_minivit_sharenum2.yaml` | `mini-swin-base-46m.pth` |
| `base-384` | `configs/swin_base_patch4_window7_224to384_minivit_sharenum2_adamw.yaml` | `mini-swin-base-224to384.pth` |

The Mini-Swin configs set `MODEL.TYPE: swin_minivit_distill`; the builder routes that to `SwinTransformerMiniViTDistill`.

### 2. Validate data

Mini-Swin supports folder splits, tar archives, and a zip/annotation mode. Most MiniViT recipes use standard ImageNet folder or tar layouts. Use `--load_tar` for tar archives; do not confuse this with Mini-DeiT's hyphenated `--load-tar` flag.

### 3. Distillation training

Mini-Swin distillation combines:

1. weight-transform flags: `--is_sep_layernorm --is_transform_heads --is_transform_ffn`,
2. teacher distillation flags: `--do_distill --alpha 0.0 --teacher /path/to/teacher.pth`, and
3. attention/hidden losses: `--attn_loss --hidden_loss --hidden_relation --student_layer_list ... --teacher_layer_list ... --hidden_weight 0.1`.

Default layer-list schedules:

| Student variant | Student layers | Teacher layers |
| --- | --- | --- |
| Tiny | `11_9_7_5_3_1` | `23_21_15_9_3_1` |
| Small | `23_21_15_9_3_1` | `23_21_15_9_3_1` |
| Base | `23_21_15_9_3_1` | `23_21_15_9_3_1` |

Keep student and teacher list lengths equal; the code pairs them by position for attention/hidden losses.

### 4. Base 224-to-384 finetune

Use the Base 224-to-384 config plus weight-only resume:

- `--cfg configs/swin_base_patch4_window7_224to384_minivit_sharenum2_adamw.yaml`
- `--resume /path/to/base_224_checkpoint.pth`
- `--resume_weight_only`
- `--train_224to384`
- normally `--batch-size 16 --accumulation-steps 2`

This activates resolution-mismatch handling for relative-position entries and classifier shapes.

## Command construction

Use the helper to print command templates without running them:

```bash
python ../scripts/build_minivit_command.py --workflow mini-deit-eval --variant tiny --data-path /path/to/ImageNet --checkpoint /path/to/mini_deit_tiny_patch16_224.pth
```

Read [`command-reference.md`](command-reference.md) for command details and [`troubleshooting.md`](troubleshooting.md) for failures.
