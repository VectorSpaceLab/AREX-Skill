---
name: model-inference
description: "Construct, inspect, and troubleshoot SSD300 model inference
  internals for the ssd.pytorch repository."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# model-inference

Use this sub-skill when a task needs to construct or inspect the SSD300 model, its prior boxes, multibox heads, detection decode/NMS path, single-image inference preprocessing, or pretrained weight compatibility.

## When to use

- Build or inspect `build_ssd(phase, size=300, num_classes=21)`.
- Explain the VGG base, extra layers, L2 normalization, localization heads, confidence heads, prior boxes, decode, and NMS contracts.
- Diagnose model construction, state-dict loading, class-count/head mismatches, tensor shape/device issues, or the legacy `Detect` incompatibility on modern PyTorch.
- Plan safe single-image inference preprocessing and postprocessing without overclaiming that test-phase inference works unchanged on modern PyTorch.

## Route elsewhere

- Dataset roots, VOC/COCO layout, annotation transforms, augmentation, dataloaders, and training commands: `../data-training/SKILL.md`.
- `eval.py`, `test.py`, notebook demo, webcam demo, VOC result files, and runnable evaluation/demo command workflows: `../evaluation-demos/SKILL.md`.

## Start here

1. Read `references/model-api.md` for signatures, model components, config facts, tensor shapes, and output contracts.
2. Read `references/inference-workflow.md` before loading weights or performing single-image inference; it includes the safe construction path and the modern PyTorch detection-layer decision point.
3. Read `references/troubleshooting.md` when imports, phases, state dicts, devices, or test-phase forward passes fail.
4. Use the bundled scripts for focused, low-cost checks:

```bash
python scripts/inspect_model_shapes.py --num-classes 21
python scripts/inspect_model_shapes.py --num-classes 21 --phase train --run-forward
python scripts/check_box_utils.py
```

The scripts assume they are run from a checkout or environment where the repository source modules are importable. They do not download data or weights.

## Do not overclaim

- `build_ssd('train', 300, 21)` constructs and train-phase zero forward has been observed to return `(loc, conf, priors)` with shapes `(1, 8732, 4)`, `(1, 8732, 21)`, `(8732, 4)` under a modern Torch runtime, aside from a `Variable(..., volatile=True)` warning.
- `build_ssd('test', ...)` constructs the legacy detection module, but a forward pass can fail on modern PyTorch because `Detect` subclasses `torch.autograd.Function` with an old-style instance `forward`. Patch `Detect` or use a legacy-compatible PyTorch before claiming end-to-end inference/eval works.
- Importing `ssd` or `data` may fail before model construction if the COCO label-map default path is absent; see troubleshooting for safe remedies.
