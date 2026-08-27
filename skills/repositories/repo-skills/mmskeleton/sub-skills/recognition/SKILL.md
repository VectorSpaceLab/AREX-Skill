---
name: recognition
description: "This skill provides ST-GCN skeleton action-recognition model,
  graph, configuration, checkpoint, and CLI guidance while routing data and pose
  concerns to their owning skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Recognition

Use this sub-skill when a user needs the repository's `ST_GCN_18` model, graph
layout/strategy selection, recognition train/test configuration construction,
pretrained-checkpoint alias selection, `mmskl` argument binding, or model
input/output shape guidance.

- Read [API reference](references/api-reference.md) for constructor contracts,
  graph layouts, adjacency strategies, and tensor shapes.
- Read [CLI and configuration reference](references/cli-reference.md) for
  recognition train/test patterns, flags, batch/GPU behavior, and config-path
  handling.
- Read [model zoo reference](references/model-zoo.md) for checkpoint aliases
  and the no-download boundary.
- Run the [tiny ST-GCN smoke](scripts/run_stgcn_smoke.py) for a bounded,
  download-free import/graph/forward check. It asserts finite output and the
  requested `(N, num_class)` shape; it is not training or evaluation.
- Use [troubleshooting](references/troubleshooting.md) for CUDA/compiler,
  graph/class-count, data/checkpoint, CLI, and native-NMS gates.

## Scope and routing

This sub-skill covers the recognition model and its application wiring. Route
JSON schema, annotation validation, loader/transforms, and axis conversion to
[the data-preparation skill](../data-preparation/SKILL.md). Route video input,
MMDetection, HRNet, and pose extraction to
[the pose-estimation skill](../pose-estimation/SKILL.md); successful ST-GCN
construction does not establish detector or video readiness.

The smoke deliberately creates synthetic input and never downloads data or a
checkpoint. Do not claim a complete training/evaluation run or downloaded
checkpoint verification from this sub-skill.
