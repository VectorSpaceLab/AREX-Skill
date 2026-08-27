---
name: inference-evaluation
description: "Run checkpoint-backed LaneNet inference, TuSimple batch
  evaluation, and postprocess troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Inference and Evaluation

Use this sub-skill when the task is to run or debug LaneNet checkpoint inference, TuSimple-style batch evaluation, DBSCAN/lane-fit postprocessing, or output interpretation.

## Route here for

- Single-image inference from a TensorFlow checkpoint using the image preprocessing and restore behavior expected by LaneNet.
- Batch inference/evaluation over a TuSimple `test_set/clips` image tree and saving overlay outputs.
- Diagnosing empty or black lane masks, DBSCAN clustering failures, missing remap files, checkpoint restore mismatches, and headless plotting issues.
- Understanding binary segmentation, instance embedding, clustered mask, fitted lane parameters, and saved overlay outputs.

## Route elsewhere

- Dataset conversion, list files, masks, or TFRecord generation: [data-preparation](../data-preparation/SKILL.md).
- Training, checkpoint creation, TensorBoard, or trainer configuration: [training](../training/SKILL.md).
- Frozen TensorFlow PB or MNN/mobile export: [model-export](../model-export/SKILL.md).

## Required context before acting

1. Confirm the user has a LaneNet repo checkout or equivalent source tree with `lanenet_model/`, `local_utils/`, `config/`, and the remap file available from the run working directory.
2. Confirm a TensorFlow 1.x-compatible Python environment. TensorFlow 1.15 with CUDA is verified for this skill; CPU can run inference/evaluation functionally but is slower.
3. Confirm the checkpoint path. Pretrained weights are not bundled. The checkpoint argument should normally be the TensorFlow checkpoint base path, not the `.index` or `.data-*` shard.
4. For custom images, ask whether TuSimple lane fitting is appropriate. If not, use `--with_lane_fit 0` and inspect raw clustered masks before tuning fitted curves.

## Bundled references and scripts

- Read [references/workflows.md](references/workflows.md) for single-image, batch-evaluation, checkpoint, and output workflows.
- Read [references/api-reference.md](references/api-reference.md) for postprocessor signatures, return keys, LaneNet inference outputs, and metric-helper notes.
- Read [references/troubleshooting.md](references/troubleshooting.md) when inference produces empty masks, checkpoint restore fails, batch paths crash, or plotting blocks.
- Use [scripts/test_lanenet.py](scripts/test_lanenet.py) as the bundled single-image inference wrapper.
- Use [scripts/evaluate_lanenet_on_tusimple.py](scripts/evaluate_lanenet_on_tusimple.py) as the bundled TuSimple batch-evaluation wrapper.

## Operating rules

- Do not imply pretrained weights ship with the skill or the repo checkout; obtain a checkpoint from training or a user-supplied pretrained download.
- Prefer noninteractive saving in automation. Use display only when the environment has a working GUI and blocking windows are acceptable.
- Keep inference/evaluation runs from the repository root or pass `--repo_root` to the bundled scripts so repo-relative config and remap loading resolve correctly.
- For custom data, first validate preprocessing, checkpoint compatibility, and binary segmentation before changing DBSCAN or lane-fit settings.
