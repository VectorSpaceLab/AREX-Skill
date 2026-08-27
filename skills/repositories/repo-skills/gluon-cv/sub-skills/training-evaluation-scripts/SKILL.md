---
name: training-evaluation-scripts
description: "Construct safe GluonCV training, evaluation, demo, and benchmark
  flag templates from the script zoo without executing source checkout scripts."
disable-model-invocation: true
metadata:
  disco-role: operating
  parent-skill: gluon-cv
  package: gluoncv
license: Apache 2.0
---

# GluonCV training and evaluation script workflows

Use this sub-skill when a task asks for GluonCV training, evaluation, demo, feature extraction, benchmarking, DDP/Horovod/DALI usage, or command-line flags for the script zoo: CIFAR/ImageNet classification, SSD/YOLO/Faster R-CNN/CenterNet/Mask R-CNN detection, segmentation, pose, action recognition, Monodepth2, SiamRPN/SMOT tracking, GAN, Re-ID, dataset preparation, or AutoGluon example commands.

This sub-skill turns the repository's script families into **self-contained, non-executable flag templates and checklists**. Treat original programs as evidence for flag shape, not as runtime files this skill depends on.

## Route first

Stay here for:

- Choosing a script family for training/evaluation/demo/benchmarking.
- Building a flag template and identifying required dataset/model/backend inputs.
- Explaining common flags such as `--model`, `--network`, `--dataset`, `--dataset-root`, `--data-dir`, `--gpus`, `--num-gpus`, `--batch-size`, `--num-workers`, `--epochs`, `--resume`, `--pretrained`, `--deploy`, `--quantized`, and `--config-file`.
- Deciding whether a workflow is safe to dry-run, help-only, reference-only, or requires user approval because it downloads, trains, benchmarks, or needs GPUs.

Route elsewhere when the user needs deeper API or data details:

- MXNet model names, `get_model`, `reset_class`, and inference API details: `../mxnet-model-zoo/`
- Dataset layouts, transforms, loaders, and annotation validation: `../data-transforms-datasets/`
- PyTorch action-recognition models, configs, tensor shapes, and DDP model smokes: `../torch-video-workflows/`
- AutoGluon tasks, export, ONNX, TVM, quantized deployment: `../automl-deployment-export/`

## Safe workflow

1. Identify the task family and backend: MXNet script-style workflow, Torch action-recognition config workflow, AutoGluon example, deployment/export, or dataset preparation.
2. Read `references/script-catalog.md` to classify source families as adapted, reference-only, or excluded.
3. Use `scripts/build_training_command.py` to generate a no-side-effect flag template:

   ```bash
   python scripts/build_training_command.py detection-yolo \
     --dataset voc --dataset-root /data/VOCdevkit --gpus "" --batch-size 2
   ```

4. Replace placeholders with user-provided values and verify prerequisites before any real execution in a user-provided checkout or project: dataset root, annotations, image/video files, pretrained cache/network policy, backend framework, optional dependencies, and GPU availability.
5. For CPU-safe exploration, prefer dry model/data smoke checks from sibling sub-skills before launching long jobs.
6. For real training, explicitly confirm expected runtime, write locations, and resource usage. Long workflows can create checkpoints/logs, download weights/data, and consume GPUs for hours.

## References and helper

- `references/training-and-evaluation-scripts.md` — task-family flag anatomy and adaptation patterns.
- `references/script-catalog.md` — source script family inventory, selected bundled replacement, and skip/risk decisions.
- `references/troubleshooting.md` — dataset, backend, optional dependency, OOM, resume, distributed, and cache failures.
- `scripts/build_training_command.py` — safe flag-template builder; it prints pseudo-command families and warnings but never starts training.

## Safety defaults

- Use empty `--gpus ""` or `--num-gpus 0` for CPU templates when the underlying workflow supports it.
- Do not run benchmark, DDP, Horovod, DALI, video decoding, dataset download, export, or training commands until the user confirms hardware/data/network/write side effects.
- Treat pretrained downloads as network/cache side effects. Prefer `pretrained=False` in API smoke checks and pass explicit cache/write locations for real runs when possible.
- When a source family defaults to GPU, make the GPU requirement visible and change the template only when CPU behavior is supported by that workflow.
