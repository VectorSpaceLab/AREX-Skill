---
name: training-references
description: "Use when planning or auditing TorchVision reference
  training/evaluation workflows for classification, quantization, detection,
  segmentation, video classification, optical flow, similarity learning, or
  stereo depth without launching expensive jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# TorchVision Training References

Use this sub-skill to turn TorchVision's official reference scripts into safe command plans, dataset-layout checks, and troubleshooting notes. The reference scripts are training baselines rather than stable package APIs; always treat generated commands as plans to review before running.

## Route first

- For model constructors, weight enums, or `weights.transforms()` usage, route to `../models-and-weights/`.
- For transform implementation details, TVTensors, masks, boxes, videos, or custom v2 pipelines, route to `../transforms-and-tv-tensors/`.
- For dataset constructors, downloads, codecs, and tiny fixtures, route to `../datasets-io-utils/`.
- For box utilities, NMS, ROI ops, and detection postprocessing internals, route to `../ops-and-detection/`.

## Safe workflow

1. Identify the task family: classification, quantization, detection, segmentation, video classification, optical flow, similarity learning, or stereo depth.
2. Read `references/task-command-recipes.md` for concrete command skeletons and safety labels.
3. Check `references/data-layouts-and-presets.md` for expected dataset layout, preset, and preprocessing assumptions.
4. Use `scripts/inspect_reference_args.py --list` or `--task <name>` to inspect known argument families without importing or running training code.
5. Read `references/troubleshooting.md` before advising a user to run any command that needs datasets, GPUs, distributed launch, checkpoints, or weight downloads.

## Safety labels

- Safe: listing arguments, producing command plans, and reviewing flags.
- Review required: single-process evaluation on already-prepared local data, especially when it may download weights.
- Unsafe by default: full training, distributed `torchrun`, dataset downloads, model-url download checks, release scripts, and benchmarks.

## Bundled helper

Run the helper from this sub-skill directory or provide its path explicitly:

```bash
python scripts/inspect_reference_args.py --list
python scripts/inspect_reference_args.py --task detection
python scripts/inspect_reference_args.py --task classification --format shell
```

The helper is a static summary adapted from the reference parsers. It does not import TorchVision, import the original scripts, read datasets, download weights, launch distributed jobs, or run training.
