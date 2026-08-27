---
name: autonomous-driving
description: "Guides InternImage autonomous-driving baselines for occupancy
  prediction, online HD map construction, and OpenLane-V2 command planning, data
  validation, submissions, metrics, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Autonomous Driving

Use this sub-skill when a task mentions InternImage autonomous-driving baselines, Occupancy Prediction, BEVFormerOcc, Online HD Map Construction, VectorMapNet, OpenLane-V2, topology metrics, OpenLane-V2 submissions, or mmdet3d training/evaluation command planning.

## Routes

- For choosing among the three challenge baselines and producing safe mmdet3d command templates, read [references/workflows.md](references/workflows.md) and use [scripts/build_autonomous_command.py](scripts/build_autonomous_command.py).
- For OpenLane-V2 data hierarchy, devkit APIs, prediction/submission schemas, and metric definitions, read [references/openlane-v2.md](references/openlane-v2.md) and use [scripts/validate_openlanev2_submission.py](scripts/validate_openlanev2_submission.py) on JSON submissions before converting to pickle or uploading elsewhere.
- For predictable dependency, data-layout, schema, topology, country-code, and OpenLane-V2 import failures, read [references/troubleshooting.md](references/troubleshooting.md).
- For DCNv3 source builds, CUDA/TensorRT/mmdeploy export, or broad OpenMMLab environment repair that is not specific to autonomous-driving data/schema choices, route to the sibling deployment guidance instead of duplicating it here.

## Safe defaults

- The bundled command builder only prints commands; it does not train, evaluate, download data, or mutate a checkout.
- The bundled OpenLane-V2 validator accepts JSON and performs standalone shape/metadata checks without importing the original repository.
- Full occupancy, HD-map, and OpenLane-V2 model runs require large datasets, checkpoints, a compatible OpenMMLab/mmdet3d stack, CUDA GPUs, and DCNv3 where InternImage backbones use it. Treat generated commands as plans until those prerequisites are explicitly confirmed.
