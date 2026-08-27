---
name: global-histogram-transfer
description: "Guides the Caffe-only Interactive Deep Colorization global
  histogram transfer workflow, assets, APIs, and failure modes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# global-histogram-transfer

Use this sub-skill when a task is about applying a reference image's global color histogram to a grayscale target image with Interactive Deep Colorization, explaining the global histogram notebook, or diagnosing Caffe/global model assets.

## Route first

- Read [references/workflows.md](references/workflows.md) for the distilled global histogram transfer recipe and data flow.
- Read [references/api-reference.md](references/api-reference.md) for the relevant Caffe wrapper class, method signatures, prototxt roles, and blob names.
- Read [references/troubleshooting.md](references/troubleshooting.md) when Caffe imports, global weights, blob names, reference image paths, or PyTorch expectations are confusing.
- Run [scripts/check_global_histogram_assets.py](scripts/check_global_histogram_assets.py) to check global prototxts, weight filenames, and reference-image directories without importing Caffe or downloading files.

## Boundaries

- For Caffe/PyTorch/Qt/Docker/model-download setup, route to [../setup-and-models/SKILL.md](../setup-and-models/SKILL.md).
- For local user-hint colorization, GUI operations, masks, suggested colors, or PyTorch local-hints workflows, route to [../interactive-colorization/SKILL.md](../interactive-colorization/SKILL.md).
- Do not claim this repository has a PyTorch global histogram transfer implementation. The global workflow here is Caffe-only.
- Do not treat static asset checks as proof of Caffe execution; PyCaffe and downloaded weights must be available before running the native workflow.

## Critical facts

- The global colorization wrapper is `ColorizeImageCaffeGlobDist(Xd=256)`.
- The global colorization call is `net_forward(input_ab, input_mask, glob_dist=-1)`.
- Passing `glob_dist=-1` zeroes the global conditioning blob and runs automatic colorization.
- Passing a 313-bin `glob_dist` fills `glob_ab_313_mask` and enables global histogram conditioning.
- The global statistics notebook path uses a Caffe net created from `models/global_model/global_stats.prototxt` and `models/global_model/dummy.caffemodel`, then reads `gt_glob_ab_313_drop` from the net output.
