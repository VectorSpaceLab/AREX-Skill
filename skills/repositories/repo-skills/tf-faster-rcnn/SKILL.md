---
name: tf-faster-rcnn
description: "Route TensorFlow 1.x Faster R-CNN tasks for install/build,
  VOC/COCO assets, pretrained demo inference, training/evaluation, and
  architecture/API modification in the deprecated tf-faster-rcnn repository."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# tf-faster-rcnn

Use this repo skill when a Researcher needs task-specific operating guidance for the deprecated `tf-faster-rcnn` TensorFlow 1.x Faster R-CNN implementation: environment/build triage, VOC/COCO assets, pretrained demo inference, training/evaluation commands, or model/API modifications.

This skill is self-contained guidance derived from source evidence and inspection checks. It does **not** certify full CUDA/demo/train/test execution; those require external datasets/checkpoints and a compatible TensorFlow 1.x + native-extension stack on the user's target host.

## Route by task

| User task | Read |
| --- | --- |
| Install dependencies, diagnose `nvcc`, CUDA, TensorFlow/protobuf, Cython extension, `nms.gpu_nms`, or config override failures | [installation-and-configuration](sub-skills/installation-and-configuration/SKILL.md) |
| Place/validate VOC or COCO data, demo images, pretrained checkpoint symlinks, ImageNet weights, output folders, or TensorBoard folders | [dataset-and-assets](sub-skills/dataset-and-assets/SKILL.md) |
| Plan pretrained demo inference, validate demo checkpoint path, understand VOC labels, NMS thresholds, visualization, or CPU/GPU demo caveats | [inference-and-demo](sub-skills/inference-and-demo/SKILL.md) |
| Build dry-run train/test/reval/convert commands, choose dataset/net schedule mappings, handle snapshots/resume, TensorBoard, evaluation, and benchmark caveats | [training-and-evaluation](sub-skills/training-and-evaluation/SKILL.md) |
| Inspect or modify `Network`, VGG/ResNet/MobileNet backbones, anchors, RPN/proposal layers, bbox transforms, image blobs, roidb/minibatch APIs | [api-and-architecture](sub-skills/api-and-architecture/SKILL.md) |

## Start here for common prompts

- "`pip install -e .` fails" → root is not installable; read [install/build notes](sub-skills/installation-and-configuration/references/install-build.md).
- "`nvcc` cannot be located" or "`nms.gpu_nms` missing" → read [installation troubleshooting](sub-skills/installation-and-configuration/references/troubleshooting.md).
- "What `--imdb` name should I use?" → read [data layouts](sub-skills/dataset-and-assets/references/data-layouts.md).
- "Where do I put the pretrained ResNet101 VOC07+12 demo model?" → read [model artifacts](sub-skills/dataset-and-assets/references/model-artifacts.md) and then [demo inference](sub-skills/inference-and-demo/references/demo-inference.md).
- "Generate the VOC07+12 ResNet101 test command" → use [training command builder](sub-skills/training-and-evaluation/scripts/tf_faster_rcnn_command_builder.py).
- "Change anchor scales or add a backbone" → read [architecture notes](sub-skills/api-and-architecture/references/architecture-notes.md).

## Safe bundled helpers

These helpers are designed to be read-only or dry-run by default:

```bash
python sub-skills/installation-and-configuration/scripts/check_environment.py --repo-root <repo-root>
python sub-skills/dataset-and-assets/scripts/validate_layout.py --repo-root <repo-root> --check demo-model
python sub-skills/inference-and-demo/scripts/demo_command_builder.py --repo-root <repo-root> --net res101 --dataset pascal_voc_0712 --validate-only
python sub-skills/training-and-evaluation/scripts/tf_faster_rcnn_command_builder.py test --dataset pascal_voc_0712 --net res101 --gpu-id 0
python sub-skills/api-and-architecture/scripts/inspect_source_api.py --repo-root <repo-root> --strict
```

Run them from the generated skill directory or pass the script path explicitly. They do not download data, fetch checkpoints, start TensorFlow model execution, or train/evaluate models unless a sub-skill explicitly says otherwise.

## Cross-cutting facts

- The project is deprecated and follows TensorFlow r1.x syntax (`tf.Session`, `tf.contrib.slim`, `tf.py_func`, `tf.to_int32`).
- The repository root has no `setup.py`/`pyproject.toml`; native extension setup is under `lib/setup.py`.
- `lib/setup.py` requires `CUDAHOME` or `nvcc` at setup import time and builds `utils.cython_bbox`, `nms.cpu_nms`, and `nms.gpu_nms`.
- `cfg.USE_GPU_NMS` defaults to `True`, and `model.nms_wrapper` imports both GPU and CPU NMS modules eagerly.
- Default anchor scales/ratios are `[8,16,32]` and `[0.5,1,2]`; source inspection verified nine anchors per location.
- Full train/test/demo workflows need external VOC/COCO data, ImageNet or trained checkpoints, old TensorFlow compatibility, and usually a CUDA-capable native build.

## Repo-level references

- [repo-provenance.md](references/repo-provenance.md): source commit, dirty-state baseline, package/version facts, and evidence paths for staleness checks.
- [troubleshooting.md](references/troubleshooting.md): cross-sub-skill symptom router for install, data, inference, training, and API failures.
- [capability-map.md](references/capability-map.md): coverage/depth summary, verification limits, and which sub-skill owns each capability.

## Boundaries

- Do not use this skill for modern TensorFlow 2 object detection, Detectron2/MMDetection, Mask R-CNN/FPN codebases, or multi-GPU TensorPack Faster R-CNN unless the user is explicitly comparing them to this repository.
- Do not claim benchmark AP reproduction from this skill alone. Treat README numbers as historical targets that require native verification.
- Do not import this skill into the live repo-skill library for this production run; the user requested `not import`.
