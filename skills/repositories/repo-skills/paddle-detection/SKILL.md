---
name: paddle-detection
description: "Guides PaddleDetection object detection, segmentation, keypoint,
  multi-object tracking, configuration, training, evaluation, inference, export,
  deployment, and PP-Human/PP-Vehicle pipeline workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaddleDetection

Use this skill when a task names PaddleDetection, `paddledet`, PP-YOLO/PP-YOLOE/PicoDet, PaddleDetection YAML configs, `tools/train.py`, `tools/infer.py`, model export, PP-Human, PP-Vehicle, PP-Tracking, or PaddleDetection deployment.

This is an operating router, not a copy of the repository. Work against the user's PaddleDetection checkout or installed package, and use the bundled references/scripts in this skill for decisions and preflight checks. Do not assume the creation checkout or its private environment still exists.

## First route

1. Identify the task family and choose exactly one primary route below.
2. Establish the target checkout/package version, PaddlePaddle device, dataset layout, config path, weights source, and whether network/GPU/vendor runtimes are allowed.
3. Run the bundled environment preflight before importing deep modules: [`scripts/check_paddledet_environment.py`](scripts/check_paddledet_environment.py).
4. Keep `use_gpu=false` or `--device=CPU` for a deterministic smoke test unless CUDA/TensorRT is explicitly required and available.
5. Read [`references/troubleshooting.md`](references/troubleshooting.md) whenever imports, weights, config paths, optional dependencies, or device checks fail.

## Routes

- **Choose a model, inspect or override YAML, use the registry, or list model families:** read [`sub-skills/model-zoo-and-configuration/SKILL.md`](sub-skills/model-zoo-and-configuration/SKILL.md).
- **Prepare COCO/VOC/WIDER/MOT/keypoint/custom data, convert annotations, validate paths, split semi-supervised data, or slice small-object data:** read [`sub-skills/data-preparation/SKILL.md`](sub-skills/data-preparation/SKILL.md).
- **Train, fine-tune, resume, evaluate, run repository inference, use distributed launch, AMP, VisualDL/W&B, or troubleshoot `tools/*.py`:** read [`sub-skills/training-evaluation-inference/SKILL.md`](sub-skills/training-evaluation-inference/SKILL.md).
- **Export a trained model or deploy with Paddle Inference, Serving, Lite, ONNX, FastDeploy, or TensorRT:** read [`sub-skills/deployment-and-export/SKILL.md`](sub-skills/deployment-and-export/SKILL.md).
- **Run PP-Human, PP-Vehicle, PP-Tracking, ReID, plate/attribute/action/violation analysis, or image/video/RTSP pipelines:** read [`sub-skills/industrial-pipelines/SKILL.md`](sub-skills/industrial-pipelines/SKILL.md).

## Package baseline

The distribution is `paddledet` and the primary import is `ppdet`. The repository's baseline requirements include PaddleDetection utilities plus NumPy below 2, OpenCV, PyYAML, Shapely, SciPy, pycocotools, VisualDL, MOT dependencies, and image augmentation utilities. Install a compatible PaddlePaddle CPU or GPU build first, then install the repository requirements and the package in editable mode when working from source.

Minimal import check:

```bash
python -c "import paddle, ppdet; print(paddle.__version__, ppdet.__version__)"
python -c "import paddle; paddle.utils.run_check()"
```

The source checkout currently advertises package version `0.0.0` even when its Git tag is newer. Treat `ppdet.model_zoo.get_config_file()` as a network/cache operation and prefer a checked-out config path for source workflows; see the model-zoo route for the observed 404 failure mode.

## Shared operating rules

- Configs are YAML and may recursively merge `_BASE_` files. Use `-o key=value` only for deliberate, logged overrides; verify paths and `num_classes` after merging.
- Weights may be local files or remote URLs. Never download weights or datasets without explicit network approval; record the exact source and checksum when reproducibility matters.
- CPU checks validate parsing/import/data contracts only. They do not prove CUDA, TensorRT, Paddle Lite, Serving, FastDeploy, or vendor accelerator behavior.
- Treat training, benchmark, full pipeline, and TIPC commands as expensive unless a tiny fixture and explicit runtime budget are available.
- Keep generated outputs outside the source tree when possible: checkpoints under a chosen `save_dir`, inference exports under a separate `output_inference`-style directory, and visualizations/results under a separate output directory.
- Before changing a config, inspect the dataset reader, metric, input shape, class count, device flags, and pretrained/weights fields together.

Read [`references/install-and-environment.md`](references/install-and-environment.md) for supported dependency variants and backend boundaries, [`references/verification-candidates.md`](references/verification-candidates.md) for safe checks, and [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is stale.
