---
name: inference
description: "Use pix2pixHD checkpointed inference, HTML result generation, and
  optional ONNX/TensorRT export or runtime paths."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Inference

Use this sub-skill for pix2pixHD test-time synthesis, result browsing, checkpoint preflight, and the optional accelerator/export paths.

## Route here for

- `test.py` runs that synthesize images from a trained checkpoint.
- `--how_many`, `--results_dir`, `--which_epoch`, `--phase`, and checkpoint-name selection.
- 512p and 1024p inference recipes adapted from `scripts/test_512p.sh`, `scripts/test_1024p.sh`, `scripts/test_512p_feat.sh`, and `scripts/test_1024p_feat.sh`.
- Feature-conditioned inference with `--instance_feat`, `--label_feat`, `--load_features`, `--cluster_path`, and `--use_encoded_image`.
- `--export_onnx`, `--engine`, and `--onnx` only as optional, reference-only paths.

## Start with

1. [Workflows](references/workflows.md) for the recipe table and result-location map.
2. [check_checkpoint.py](scripts/check_checkpoint.py) to preflight the expected checkpoint files and feature-cache paths.
3. [CLI reference](references/cli-reference.md) for flag defaults, hard-coded test-time overrides, and output locations.
4. [Accelerated inference](references/accelerated-inference.md) for ONNX/TensorRT caveats and legacy helper limits.
5. [Troubleshooting](references/troubleshooting.md) for missing checkpoints, HTML/dependency issues, feature-ordering mistakes, and optional-backend failures.

## Expected outputs

- HTML results at `results_dir/name/phase_which_epoch/index.html`.
- Rendered images under `results_dir/name/phase_which_epoch/images/`.
- Generator checkpoint at `checkpoints_dir/name/which_epoch_net_G.pth`.
- Optional encoder checkpoint `which_epoch_net_E.pth` when feature guidance uses `netE`.
- Optional sampled-feature cache at `checkpoints_dir/name/cluster_path`.

## Boundaries

- For dataset layout, paired label/instance/image folders, and `dataroot` conventions, use [setup-and-data](../setup-and-data/SKILL.md).
- For feature cache creation, clustering, and `load_features` workflow details, use [instance-features](../instance-features/SKILL.md).
- For checkpoint naming and save/load behavior, use [training](../training/SKILL.md).
- Do not cover training-loop, loss, optimizer, or dataset-authoring details here.
- Do not present TensorRT/ONNX as the default supported path; keep it clearly optional.

## Helper scripts

- [build_inference_command.py](scripts/build_inference_command.py) prints safe commands from an explicit `--repo-root`.
- [check_checkpoint.py](scripts/check_checkpoint.py) checks checkpoint and feature-cache expectations before a run.

## Fast recipes

- 512p labels only: `python test.py --name label2city_512p`
- 1024p labels only: `python test.py --name label2city_1024p --netG local --ngf 32 --resize_or_crop none`
- 512p feature-conditioned: `python encode_features.py --name label2city_512p_feat`; then `python test.py --name label2city_512p_feat --instance_feat`
- 1024p feature-conditioned: `python encode_features.py --name label2city_1024p_feat --netG local --ngf 32 --resize_or_crop none`; then `python test.py --name label2city_1024p_feat --netG local --ngf 32 --resize_or_crop none --instance_feat`
- Encoded-image feature inference: add `--use_encoded_image` to a feature-enabled command when the real image should be encoded instead of using clustered features.
- ONNX export: `python test.py --name <exp> --export_onnx <file.onnx>`
- TensorRT/ONNX runtime: see [accelerated inference](references/accelerated-inference.md)
