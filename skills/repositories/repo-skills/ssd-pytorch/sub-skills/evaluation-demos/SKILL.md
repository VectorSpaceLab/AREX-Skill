---
name: evaluation-demos
description: "Plan VOC evaluation, test-output inspection, notebook demos, and
  webcam prerequisites for ssd.pytorch."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# evaluation-demos

Use this sub-skill when the task is to plan or diagnose ssd.pytorch evaluation,
text test outputs, notebook-style image demos, or live webcam demos.

## Choose this sub-skill for

- VOC2007 mAP evaluation command planning with `eval.py`.
- Prediction/ground-truth text dump planning with `test.py`.
- Understanding result file formats, AP summaries, confidence thresholds, top-k
  choices, and evaluation output locations.
- Checking static demo prerequisites for notebook and live webcam workflows.
- Explaining why full mAP reproduction requires both VOC2007 test data and a
  compatible trained SSD300 VOC weight file.

## Do not handle here

- Dataset download, VOC directory repair, or dataset layout validation beyond
  naming the required VOC2007 files. Route that work to `../data-training/SKILL.md`.
- Model construction, SSD weight/key compatibility, or modern PyTorch
  `Detect(Function)` patching. Route that work to `../model-inference/SKILL.md`.
- Opening a webcam, displaying GUI windows, or running a full mAP benchmark from
  this skill's bundled scripts.

## Fast workflow

1. Read [references/evaluation-and-test.md](references/evaluation-and-test.md)
   before planning `eval.py` or `test.py` runs.
2. Use [scripts/plan_evaluation_command.py](scripts/plan_evaluation_command.py)
   to print a safe command template without executing the repository scripts.
3. Read [references/demo-workflows.md](references/demo-workflows.md) before
   notebook or webcam demo work.
4. Use [scripts/check_demo_requirements.py](scripts/check_demo_requirements.py)
   for import-only checks of `torch`, `cv2`, `imutils`, Jupyter components, and
   optional CUDA availability. It does not access a camera or open a GUI window.
5. If an attempted evaluation or demo fails, first classify the symptom with
   [references/troubleshooting.md](references/troubleshooting.md), then route
   model or dataset fixes to the sibling sub-skill named above.

## Required planning inputs

- `trained_model`: path to a compatible SSD300 VOC `.pth` state_dict.
- `voc_root`: VOCdevkit root for VOC2007 test/val data when using evaluation or
  dataset-backed notebook examples.
- `save_folder`: output folder for `test.py` and parser-created evaluation
  folders; use a trailing separator for `test.py` legacy string concatenation.
- CUDA intent: CPU-only, CUDA if available, or CUDA required.
- Threshold intent: low confidence for mAP, higher visual thresholds for demos.

## Safety defaults

- Do not promise the README mAP values unless VOC2007 test data, compatible
  weights, dependency versions, and legacy model-forward compatibility are all
  verified in the runtime environment.
- Prefer CPU command templates when hardware is unknown.
- Treat webcam and notebook demos as optional demonstrations, not benchmark
  evidence.
