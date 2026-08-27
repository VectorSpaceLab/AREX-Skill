# Checkpoints and Configs

AnyDoor uses small YAML config files with placeholder checkpoint and data paths.
Future agents should patch those placeholders before trying inference, demo,
training, or conversion workflows.

## Core config files

| File | Purpose | Important fields |
| --- | --- | --- |
| `configs/anydoor.yaml` | Model architecture and DINOv2 conditioning | `model.target`, `control_stage_config`, `unet_config`, `first_stage_config`, `cond_stage_config.weight` |
| `configs/inference.yaml` | Inference checkpoint and model config | `pretrained_model`, `config_file`, `save_memory` |
| `configs/demo.yaml` | Demo checkpoint and UI toggles | `pretrained_model`, `config_file`, `save_memory`, `use_interactive_seg` |
| `configs/datasets.yaml` | Training and test dataset paths | `Train.*`, `Test.*` path roots and annotation files |

## Placeholder values to replace

- `path/epoch=1-step=8687.ckpt` in `configs/inference.yaml` and
  `configs/demo.yaml`
- `path/dinov2_vitg14_pretrain.pth` in `configs/anydoor.yaml`
- dataset roots such as `path/YTBVOS/...`, `path/TryOn/VitonHD/...`,
  `path/COCO/train2017`, and the other values in `configs/datasets.yaml`

## Checkpoint facts from the source

- The DINOv2 conditioning encoder is `ldm.modules.encoders.modules.FrozenDinoV2Encoder`.
- That encoder reads the DINOv2 checkpoint from the `cond_stage_config.weight`
  field in `configs/anydoor.yaml`.
- `run_inference.py` and `run_gradio_demo.py` both expect a pretrained AnyDoor
  checkpoint path from their respective YAML files.
- `predict.py` has a separate download/cache path for the Replicate Cog flow.

## What the configs imply

- `configs/anydoor.yaml` defines the model graph rather than a tiny wrapper.
- The repo assumes a 512x512 generation space.
- The conditioning image size is 224x224.
- The control tensor includes a collage image plus a mask channel.
- The dataset config mixes video, image, saliency, try-on, SAM, and LVIS style
  sources.

## Safe patching policy

Use the bundled config patcher rather than editing randomly:

- replace placeholder checkpoint values explicitly,
- keep a dry-run mode when you only need to inspect the changes,
- do not rewrite unrelated YAML fields,
- and do not embed local machine paths in the public skill content.

## Signs that config patching is incomplete

- import succeeds but generation fails immediately on a missing checkpoint,
- the demo launches with refinement toggles but no weights are present,
- the DINOv2 encoder cannot find its weight file,
- or the training loader fails because dataset roots still contain placeholder
  strings.

## Related references

- Read `references/environment-and-installation.md` before patching.
- Read `references/troubleshooting.md` for the most common path and checkpoint
  errors.
