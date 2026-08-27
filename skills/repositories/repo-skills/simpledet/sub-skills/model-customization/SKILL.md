---
name: model-customization
description: "Guides SimpleDet symbolic detector composition, config-first model
  changes, component contracts, model-family selection, and custom operator or
  checkpoint compatibility decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model customization

Use this route when a task asks to add or change a detector, backbone, neck, RPN,
RoI extractor, bbox/mask head, metric, custom operator, or model-family config.
Read [architecture-api.md](references/architecture-api.md) for contracts and
[model-families.md](references/model-families.md) for family routing.

## Config-first versus code

Start with a copied config for exposed parameters: backbone depth, FPN/neck,
anchors, proposal limits, ROI shape, class count, normalizer, FP16, schedule,
dataset split, NMS, or checkpoint prefix. Use code only for new symbols,
inputs/labels, custom operators, losses, branches, or output contracts. Read
[customization-workflows.md](references/customization-workflows.md) for the
sequence and [troubleshooting.md](references/troubleshooting.md) for shape/name
and operator failures.

## Architecture route

The usual composition is `Backbone -> Neck -> RpnHead -> RoiExtractor ->
BboxHead`, with optional `MaskHead`, detector, postprocessor, metric, and input
transform. Detector classes expose train/test symbol methods; configs own the
actual composition and returned data/label names. External `mxnext` TVM/custom
operators and CUDA support are required for many families, so source inspection
is not runtime proof.

Use [scripts/list_model_families.py](scripts/list_model_families.py) to inventory
available family/config signals without importing MXNet or constructing symbols.
Route actual execution through [detection-workflows](../detection-workflows/SKILL.md)
and backend setup through [setup-and-operations](../setup-and-operations/SKILL.md).
