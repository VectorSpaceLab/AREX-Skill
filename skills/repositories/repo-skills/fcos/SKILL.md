---
name: fcos
description: "Routes FCOS object-detection repo tasks for inference demos,
  config/data setup, training/evaluation, ONNX export, and legacy PyTorch
  internals."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# FCOS Repo Skill

Use this skill when a task is about **FCOS: Fully Convolutional One-Stage Object Detection**, the legacy PyTorch/maskrcnn-benchmark implementation for anchor-free object detection. It covers using the public `fcos` package/API, selecting and validating configs, preparing dataset layouts, building training/evaluation commands, exporting ONNX models, and maintaining FCOS internals.

## First Checks

1. Confirm the user is asking about FCOS-style object detection, FCOS configs, `fcos` / `fcos_core`, maskrcnn-benchmark-derived training scripts, or errors such as missing `fcos_core._C`.
2. Check the runtime with [`scripts/check_fcos_environment.py`](scripts/check_fcos_environment.py) when import, CUDA, extension, or config availability matters.
3. Read [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill matches a current checkout or should be refreshed.
4. For cross-cutting install/import/build failures, read [`references/troubleshooting.md`](references/troubleshooting.md) before changing code or dependencies.

## Public Package Baseline

FCOS is a legacy source-install package named `fcos` with import roots `fcos` and `fcos_core`. A practical installation usually needs:

```bash
pip install torch torchvision ninja yacs cython matplotlib tqdm opencv-python scikit-image
pip install git+https://github.com/tianzhi0549/FCOS.git
python - <<'PY'
from fcos_core.config import cfg
print(cfg.MODEL.FCOS_ON)
PY
```

For real model inference/training, a compiled `fcos_core._C` extension and a PyTorch/CUDA combination compatible with this older maskrcnn-benchmark code are required. Modern PyTorch releases can need compatibility patches; do not promise that a CPU import proves real detector inference.

## Route Map

- **Image inference, demos, and public `FCOS` API** → [`sub-skills/inference-demo/SKILL.md`](sub-skills/inference-demo/SKILL.md). Use this for installed `fcos` CLI usage, `FCOS.detect`, model-name choices, image preprocessing, CPU/GPU selection, output boxes, visualization, and demo troubleshooting.
- **Training, evaluation, distributed launch, checkpoints** → [`sub-skills/training-evaluation/SKILL.md`](sub-skills/training-evaluation/SKILL.md). Use this for `--config-file`, `MODEL.WEIGHT`, `OUTPUT_DIR`, `TEST.IMS_PER_BATCH`, multi-GPU launch, OOM mitigation, and stripping solver states.
- **Configs, model catalog, and dataset layouts** → [`sub-skills/data-configs/SKILL.md`](sub-skills/data-configs/SKILL.md). Use this for `configs/fcos` selection, `MODEL.FCOS` keys, COCO/VOC/Cityscapes layout validation, custom dataset planning, and config merge diagnostics.
- **ONNX export and ONNX evaluation planning** → [`sub-skills/onnx-export/SKILL.md`](sub-skills/onnx-export/SKILL.md). Use this for FCOS ONNX export commands, output tensor names, dummy input constraints, and Caffe2/backend limitations.
- **Source internals and repo maintenance** → [`sub-skills/internals-maintenance/SKILL.md`](sub-skills/internals-maintenance/SKILL.md). Use this for FCOS head/loss/postprocess internals, `BoxList`, compiled extension issues, tests, and porting to newer PyTorch.

## Common Decisions

- If the user only wants to detect objects in one image, route to `inference-demo` and prefer the high-level `fcos.FCOS` API or the installed `fcos` CLI.
- If the user mentions COCO/VOC/Cityscapes paths, config overrides, class counts, or YAML errors, route to `data-configs` before training.
- If the user asks for AP numbers, model weights, batch sizes, or an evaluation command, route to `training-evaluation` and remind them that datasets and weights are not bundled.
- If the user asks for ONNX, do not treat it as normal PyTorch evaluation; route to `onnx-export` because the export script emits backbone/head tensors and the test script does PyTorch post-processing.
- If the user is editing FCOS code or seeing `_C`, compiler, `torch._six`, `libc10`, or NumPy ABI errors, route to `internals-maintenance` plus the root troubleshooting reference.

## Safety and Scope Notes

- Do not download pretrained weights, datasets, or run long training/evaluation unless the user approves the cost and runtime.
- Do not open GUI windows or webcams by default; use no-display/API paths for automated agents.
- Do not claim benchmark reproduction unless the required dataset, weights, compiled extension, and GPU runtime were actually verified.
- The bundled scripts are safe diagnostics and command builders. They are replacements for routine guidance, not large model weights or datasets.
