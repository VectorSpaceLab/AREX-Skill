---
name: graph-and-embedding-plugins
description: "Operate tensorboardX graph visualization and embedding projector workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Graph And Embedding Plugins

Use this sub-skill when a task involves tensorboardX graph visualization or the TensorBoard projector plugin:

- `SummaryWriter.add_graph` for PyTorch `torch.nn.Module` graphs, including CPU-only tracing, tuple/list inputs, `verbose`, and `use_strict_trace` decisions.
- `SummaryWriter.add_onnx_graph` for an existing local ONNX model file.
- `SummaryWriter.add_openvino_graph` for an existing local OpenVINO IR XML file.
- `SummaryWriter.add_embedding` for projector tensors, metadata, metadata headers, label-image sprites, `global_step`, and `tag` layout.
- Troubleshooting graph/plugin failures, optional dependencies, and projector file layout mistakes.

## Route Boundaries

- Route writer creation, log directory policy, flushing, closing, purging, and event-file lifecycle to `logging-core`.
- Route general image, audio, video, figure, mesh, or rich-media encoding to `rich-media-summaries`; keep only projector `label_img` sprite handling here.
- Route remote projector paths such as S3 or GCS buckets, cloud credentials, and parallel writers to `remote-and-parallel-integrations`.
- Do not depend on source checkout examples, tests, network model downloads, or external fixtures for runtime use. Use the bundled scripts in this sub-skill for local smoke checks.

## Operating Map

1. Identify the target plugin path: PyTorch graph, ONNX graph, OpenVINO graph, or projector embedding.
2. Check the method contract and optional dependencies in [references/api-reference.md](references/api-reference.md).
3. Follow an end-to-end workflow in [references/workflows.md](references/workflows.md).
4. For projector output paths, metadata/header rules, and label-image sprite constraints, use [references/data-formats.md](references/data-formats.md).
5. For failures, use [references/troubleshooting.md](references/troubleshooting.md) before changing the model, tensors, metadata, or log directory.

## Bundled Smoke Scripts

- [scripts/tbx_graph_smoke.py](scripts/tbx_graph_smoke.py): tiny CPU PyTorch graph smoke with dependency guards.
- [scripts/tbx_projector_smoke.py](scripts/tbx_projector_smoke.py): tiny embedding projector smoke with metadata header and square label images.
- [scripts/tbx_onnx_openvino_smoke.py](scripts/tbx_onnx_openvino_smoke.py): local OpenVINO XML smoke plus optional local ONNX-file smoke; performs no network access.

CPU is enough for these workflows unless the user deliberately traces a GPU model or passes GPU tensors. If GPU is used, keep the module parameters and every input tensor on the same device.