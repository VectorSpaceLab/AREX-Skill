# MiniViT Command Reference

## Helper script

The helper prints shell command templates only:

```bash
python ../scripts/build_minivit_command.py --help
```

Required template families:

- `mini-deit-train`
- `mini-deit-eval`
- `mini-swin-train`
- `mini-swin-eval`
- `mini-swin-finetune-384`

It also supports a Mini-DeiT Base-384 finetune template for convenience. The helper does not start distributed training or write files.

## Mini-DeiT examples

Train a Tiny template:

```bash
python ../scripts/build_minivit_command.py --workflow mini-deit-train --variant tiny --data-path /path/to/ImageNet --output /path/to/out --teacher-path /path/to/regnety_160.pth
```

Evaluate Base-384:

```bash
python ../scripts/build_minivit_command.py --workflow mini-deit-eval --variant base-384 --data-path /path/to/ImageNet --checkpoint /path/to/mini_deit_base_patch16_384.pth
```

Key flags:

| Flag | Meaning |
| --- | --- |
| `--model mini_deit_*` | TimM-registered Mini-DeiT model name. |
| `--data-path` | ImageNet root; folder or tar layout. |
| `--output_dir` | Output location used if the printed command is run. |
| `--teacher-model regnety_160` | Documented teacher architecture for soft distillation. |
| `--teacher-path` | Optional local teacher checkpoint to avoid implicit downloads. |
| `--resume --eval` | Evaluation checkpoint and eval-only mode. |
| `--load-tar` | Mini-DeiT tar-layout flag. |

## Mini-Swin examples

Train Tiny with Apex disabled:

```bash
python ../scripts/build_minivit_command.py --workflow mini-swin-train --variant tiny --data-path /path/to/ImageNet --output /path/to/out --teacher /path/to/swin_teacher.pth --amp-opt-level O0
```

Evaluate Small:

```bash
python ../scripts/build_minivit_command.py --workflow mini-swin-eval --variant small --data-path /path/to/ImageNet --checkpoint /path/to/mini-swin-small-26m.pth --amp-opt-level O0
```

Finetune Base 224 to 384:

```bash
python ../scripts/build_minivit_command.py --workflow mini-swin-finetune-384 --data-path /path/to/ImageNet --output /path/to/out --checkpoint /path/to/mini-swin-base-224.pth --amp-opt-level O0
```

Key flags:

| Flag | Meaning |
| --- | --- |
| `--cfg` | YAML config for the selected Mini-Swin variant. |
| `--data-path` | ImageNet root. |
| `--output` / `--tag` | Output root and experiment tag used if the command is run. |
| `--is_sep_layernorm --is_transform_heads --is_transform_ffn` | MiniViT weight-sharing transformation options. |
| `--do_distill --teacher` | Teacher-student distillation. |
| `--attn_loss --hidden_loss --hidden_relation` | Distillation loss taps. |
| `--student_layer_list --teacher_layer_list` | Underscore-separated layer IDs used by loss taps. |
| `--load_tar` | Mini-Swin tar-layout flag. |
| `--resume_weight_only --train_224to384` | Required for Base 224-to-384 finetuning. |

## Variant mapping

| Helper variant | Mini-DeiT model | Mini-Swin config |
| --- | --- | --- |
| `tiny` | `mini_deit_tiny_patch16_224` | `configs/swin_tiny_patch4_window7_224_minivit_sharenum6.yaml` |
| `small` | `mini_deit_small_patch16_224` | `configs/swin_small_patch4_window7_224_minivit_sharenum2.yaml` |
| `base` | `mini_deit_base_patch16_224` | `configs/swin_base_patch4_window7_224_minivit_sharenum2.yaml` |
| `base-384` | `mini_deit_base_patch16_384` | `configs/swin_base_patch4_window7_224to384_minivit_sharenum2_adamw.yaml` |
