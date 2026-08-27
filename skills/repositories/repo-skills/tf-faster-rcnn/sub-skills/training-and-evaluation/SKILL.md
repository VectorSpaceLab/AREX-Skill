---
name: training-and-evaluation
description: "Train, test, re-evaluate, and convert tf-faster-rcnn experiments
  safely with schedule-aware command construction, config overrides, snapshot
  handling, output paths, and evaluation caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Training and Evaluation

Use this sub-skill when a Researcher needs to plan, dry-run, diagnose, or deliberately launch tf-faster-rcnn training, validation, testing, re-evaluation, or deprecated VGG16 snapshot conversion.

## Route here for

- Expanding `train_faster_rcnn.sh`, `test_faster_rcnn.sh`, and `convert_vgg16.sh` behavior into explicit `tools/trainval_net.py`, `tools/test_net.py`, `tools/reval.py`, or `tools/convert_from_depre.py` commands.
- Choosing the repository's dataset schedule mapping for `pascal_voc`, `pascal_voc_0712`, or `coco`, including train/test imdb names, iteration counts, learning-rate step, anchors, and ratios.
- Choosing a supported network selector: `vgg16`, `res50`, `res101`, `res152`, or `mobile`, while checking whether a matching config file exists in the user's checkout.
- Applying safe config overrides through the repository's `--set KEY VALUE ...` grammar and predicting the output tag that shell launchers would derive from extra arguments.
- Reasoning about snapshots, resume behavior, TensorBoard directories, test output directories, re-evaluation from `detections.pkl`, and deprecated VGG16 conversion.
- Diagnosing missing initialization weights, missing trained checkpoints, NaNs, stale snapshots, NMS/AP mismatches, and expensive-run blockers.

## Route elsewhere

- Installation, TensorFlow/CUDA compatibility, Cython extension builds, `USE_GPU_NMS`, and environment checks belong in [installation-and-configuration](../installation-and-configuration/SKILL.md).
- VOC/COCO directory layouts, dataset registry details, ImageNet initialization checkpoint placement, and pretrained model artifact layouts belong in [dataset-and-assets](../dataset-and-assets/SKILL.md).
- Demo-only image inference and visualization on custom images belongs in [inference-and-demo](../inference-and-demo/SKILL.md).
- Low-level network, RPN, RoI, bbox, and model-extension APIs belong in [api-and-architecture](../api-and-architecture/SKILL.md).
- Cross-cutting repo issues should also consult the root troubleshooting reference when it exists: [root troubleshooting](../../references/troubleshooting.md).

## First safety rule

Do not start a real train/test/evaluation run while only trying to answer a planning question. Full training and benchmark evaluation are expensive and require external datasets, checkpoints, a compatible TensorFlow 1.x runtime, and usually compiled CUDA/NMS extensions. Use the bundled dry-run builder first:

```bash
python sub-skills/training-and-evaluation/scripts/tf_faster_rcnn_command_builder.py train --dataset pascal_voc_0712 --net res101 --gpu-id 0
```

The builder prints commands only; it never trains or evaluates by itself.

## Read in this order

1. [training-evaluation.md](references/training-evaluation.md) for workflow semantics, schedule mappings, output directories, snapshots/resume, TensorBoard, benchmark caveats, and failure recovery.
2. [cli-reference.md](references/cli-reference.md) for command-line options, override grammar, and command-builder examples.
3. [troubleshooting.md](references/troubleshooting.md) for targeted diagnosis of missing data/weights, NaNs, stale snapshots, NMS/AP surprises, and expensive-run blocks.

## Evidence-backed limits

- Full CUDA build, demo, train, test, and benchmark AP reproduction were not verified during skill production. CPU/source inspection verified command facts, config behavior, dataset registry facts, anchor/NMS utility behavior, and TensorFlow 1.15 CPU import as an inspection substitute for the TensorFlow r1.2-era repository.
- The repository is deprecated; benchmark numbers are historically reported, stochastic, and dependent on old TensorFlow/CUDA/native-extension behavior.
- `res152` is accepted by `tools/trainval_net.py` and `tools/test_net.py` and appears in README performance notes, but the checked-out `experiments/cfgs/` evidence did not include `res152.yml`; require a user-supplied config or cloned evidence before claiming a ready command.
