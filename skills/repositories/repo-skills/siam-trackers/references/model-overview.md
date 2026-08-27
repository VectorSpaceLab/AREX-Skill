# Model and Variant Overview

## When to read

Read this before selecting a tracker or comparing reported speed/accuracy. The
collection contains source snapshots with different configuration, dependency,
and completeness levels; names alone do not establish interchangeability.

## NanoTrack variants

| Variant | Backbone/head evidence | Tracking geometry | Reported collection facts | Required matching assets |
|---|---|---|---|---|
| V1 | MobileNetV3 path with `ban_v1` | 64-channel path, stride 16, output grid 16 | Root README reports 752K backbone ONNX, 384K head ONNX, 75.6M FLOPs, 287.9K parameters, and historical VOT/GOT-10k/DTB70 results | V1 checkpoint, V1 head, V1 config/hyperparameters |
| V2 | MobileNetV3 path with `ban_v2` | 64-channel path, stride 16, output grid 16 | Root README reports 1.0M backbone ONNX, 712K head ONNX, 84.6M FLOPs, 334.1K parameters, and historical results | V2 checkpoint, V2 head, V2 config/hyperparameters |
| V3 | `mobilenetv3_small_v3` with `ban_v3` | 96-channel path, stride 16, tracking output size 15; export reference uses template/search feature shapes 8×8/16×16 | Root README reports 1.4M backbone ONNX, 1.1M head ONNX, 115.6M FLOPs, 541.4K parameters, and historical results | V3 checkpoint, V3 head, V3 config, matching 96-channel export contract |

The metric and size values above are project-reported README evidence, not
reproduced verification. Do not present them as a result of a new run.

## NanoTrack component contract

The maintained implementation composes a backbone, optional adjustment neck,
and BAN head in `ModelBuilder`. `NanoTracker` caches the template feature on the
model, generates a point grid and Hanning window from the config, crops BGR
frames, converts logits/deltas to boxes, applies scale/aspect penalties and
window influence, then returns a bbox and best score. Load the detailed API and
state contract from the [inference route](../sub-skills/inference/SKILL.md).

The same mutable `cfg` object is merged from YAML files. Start a fresh process
when comparing variants, and load the matching head module before constructing a
model. A YAML merge does not by itself replace a previously imported head or
clear unrelated global config fields.

## Other snapshots

- `DaSiamRPN`, `SiamRPN`, and `SiamRPNpp`: Siamese region-proposal families with
  test/eval and Cython region-extension patterns in populated snapshots.
- `SiamBAN` and `SiamCAR`: box-adaptive/fully-convolutional families with
  legacy train/test workflows and old PyTorch requirements.
- `SiamFC` and `SiamFCpp`: fully-convolutional snapshots; the collection has
  both a lighter pysot-style copy and a larger video-analyst tree.
- `SiamMask`: tracking plus segmentation evidence, with additional mask data
  and model requirements.
- `SiamDW`: FC and RPN variants, with separate code roots and legacy dependency
  surfaces.
- `TrTr`: transformer tracker snapshot with configuration-specific encoder and
  decoder depth.
- `UpdateNet`: model-update workflow with template-generation/data caveats.
- `LightTrack` and `Ocean`: README/reference-only entries in this checkout, not
  local complete implementations.

Use [variant-catalog](../sub-skills/variant-catalog/SKILL.md) for the evidence
level, prerequisites, and route-selection policy. Use the dedicated NanoTrack
routes for implementation-level guidance.
