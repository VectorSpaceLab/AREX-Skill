# MiniViT Troubleshooting

## `rpe_ops` not built

**Symptom:** Importing Mini-DeiT/iRPE warns that `rpe_ops` is not built.

**Meaning:** The optional C++/CUDA iRPE index extension is missing. A Python fallback exists and is acceptable for inspection and small CPU model construction; training is slower without the extension.

**Action:**

```bash
python ../../../scripts/check_custom_ops.py --path /path/to/rpe_ops --module rpe_index
```

Build the extension only when the user needs accelerated training and has a compatible CUDA toolchain.

## Teacher checkpoint path

**Mini-DeiT:** `--teacher-path` is optional. If omitted, the training script may try to create/download a pretrained teacher. Use a local `--teacher-path` when downloads are disallowed or reproducibility matters.

**Mini-Swin:** Documented distillation recipes require `--teacher /path/to/teacher.pth`. The loader infers teacher family from the filename: names containing `regnety_160` use RegNetY; names containing `base` or `large` use Swin teacher shapes. Rename or document teacher files clearly.

## Tar versus folder ImageNet

Use the shared checker first:

```bash
python ../../../scripts/check_dataset_layout.py --root /path/to/ImageNet --kind imagenet1k
```

Mini-DeiT tar flag is `--load-tar`; Mini-Swin tar flag is `--load_tar`. Folder layouts need neither flag.

## Unknown Mini-DeiT model name

Valid Mini-DeiT names are:

- `mini_deit_tiny_patch16_224`
- `mini_deit_small_patch16_224`
- `mini_deit_base_patch16_224`
- `mini_deit_base_patch16_384`

If timm cannot find one of these, ensure the Mini-DeiT model registration module is imported before calling `create_model`. The Mini-DeiT training script imports it automatically.

## Mini-Swin config path errors

Mini-Swin requires `--cfg`; commands are intended to be run from the Mini-Swin project directory unless absolute config paths are supplied. Choose the exact config for the variant:

- Tiny: `configs/swin_tiny_patch4_window7_224_minivit_sharenum6.yaml`
- Small: `configs/swin_small_patch4_window7_224_minivit_sharenum2.yaml`
- Base: `configs/swin_base_patch4_window7_224_minivit_sharenum2.yaml`
- Base 384: `configs/swin_base_patch4_window7_224to384_minivit_sharenum2_adamw.yaml`

## Apex optional in Mini-Swin

Mini-Swin imports Apex optionally, but execution asserts Apex is present whenever `AMP_OPT_LEVEL` is not `O0`. The parser default is `O1`. If Apex is unavailable, add `--amp-opt-level O0` or install a CUDA/PyTorch-compatible Apex build.

## Layer-list mismatches

Mini-Swin parses layer lists by splitting underscores into integer IDs. Attention/hidden losses pair student and teacher lists by position. Keep lengths equal and use IDs that exist for the selected student and teacher depth.

Useful defaults:

- Tiny student: `--student_layer_list 11_9_7_5_3_1 --teacher_layer_list 23_21_15_9_3_1`
- Small/Base student: `--student_layer_list 23_21_15_9_3_1 --teacher_layer_list 23_21_15_9_3_1`

## 224-to-384 checkpoint mismatch

For Mini-Swin Base 224-to-384 finetuning, use the 224-to-384 config plus `--resume_weight_only --train_224to384`. This activates checkpoint-loading logic that tolerates resolution-sensitive relative-position entries and classifier differences.
