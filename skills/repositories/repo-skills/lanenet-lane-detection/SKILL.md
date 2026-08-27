---
name: lanenet-lane-detection
description: "Route LaneNet lane-detection tasks across data preparation,
  training, inference, and export workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# LaneNet Lane Detection

Use this skill for tasks on the MaybeShewill-CV `lanenet-lane-detection` repository: TuSimple data preparation, LaneNet training, checkpoint-backed inference and evaluation, or frozen-PB / MNN export.

## Quick route map

- **Raw TuSimple labels, masks, list files, TFRecords** → [data-preparation](sub-skills/data-preparation/SKILL.md)
- **Train or resume LaneNet** → [training](sub-skills/training/SKILL.md)
- **Run single-image inference or TuSimple batch evaluation** → [inference-evaluation](sub-skills/inference-evaluation/SKILL.md)
- **Freeze checkpoints or prepare PB/MNN export** → [model-export](sub-skills/model-export/SKILL.md)

## Read first

- [Repository provenance](references/repo-provenance.md) to confirm the source checkout state.
- [Configuration overview](references/configuration.md) for repo-root-relative config loading, default paths, and important knobs.
- [Troubleshooting](references/troubleshooting.md) for TF 1.x, protobuf, CUDA/cuDNN, placeholder-path, and checkpoint issues.
- [Workflow overview](references/workflows.md) when you need the end-to-end path rather than a single stage.
- [Environment check](scripts/check_lanenet_environment.py) for a quick preflight of imports, repo-root resolution, and GPU visibility.

## Shared operating assumptions

- The validated runtime path is Python 3.7 with TensorFlow 1.15 GPU support, CUDA 10.0, and cuDNN 7.6.
- Install `requirements.txt` plus a TensorFlow 1.15-compatible build; if TensorFlow import errors mention protobuf descriptors, pin `protobuf<=3.20.x`.
- The repo uses repo-root-relative config loading. If you are not already in the repository root, pass `--repo_root` to the bundled scripts.
- Pretrained weights are not bundled. Training produces checkpoints that inference and export consume.
- The shipped sample list files under `data/training_data_example/` still contain placeholder paths; normalize them before using them as real training input.

## How to choose a route

- If the task starts with `label*.json`, `gt_image`, `gt_binary_image`, or `gt_instance_image`, go to **data-preparation**.
- If the task mentions `tusimple_train.tfrecords`, checkpoints, mIoU, TensorBoard, or `TRAIN.*` / `SOLVER.*` config values, go to **training**.
- If the task mentions `test_lanenet.py`, `evaluate_lanenet_on_tusimple.py`, `DBSCAN_EPS`, `DBSCAN_MIN_SAMPLES`, `with_lane_fit`, or empty masks, go to **inference-evaluation**.
- If the task mentions `freeze_lanenet_model.py`, frozen `.pb`, `final_binary_output`, `final_pixel_embedding_output`, or MNN deployment, go to **model-export**.

## Shared conventions

- Run from the repo root when possible, or pass an explicit `--repo_root` to the bundled wrappers.
- Keep the original source checkout independent from the generated runtime skill: read the bundled sub-skill references and scripts instead of pointing future users back to `tools/` or `mnn_project/`.
- Use the sub-skill references for the detailed commands, config keys, and troubleshooting steps; this root file is only the router.
