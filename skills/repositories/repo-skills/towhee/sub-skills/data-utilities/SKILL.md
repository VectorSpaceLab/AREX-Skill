---
name: data-utilities
description: "Use Towhee DataCollection, Entity, DataLoader, media wrappers,
  display, serialization, and debug visualizer/profiler outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Towhee Data Utilities

Use this sub-skill when the task is about converting Towhee runtime results into inspectable rows, moving data into a pipeline, wrapping image/audio/video arrays, serializing displayed data, or reading pipeline debug visualizer/profiler outputs.

## Route here for

- `towhee.DataCollection(...)`, `towhee.datacollection.DataCollection`, `Entity`, `to_list()`, `to_dict()`, `from_dict()`, `copy()`, and `show()`.
- `towhee.DataLoader(data_source, parser=None, batch_size=None)` for iterable or callable data sources.
- `towhee.types.Image`, `AudioFrame`, `VideoFrame`, `towhee.types.image_utils.from_pil`, `to_pil`, and color conversion helpers.
- `RuntimePipeline` result conversion to `DataCollection` or list/dict rows.
- `RuntimePipeline.debug(..., profiler=True, tracer=True)` outputs, `Visualizer`, `DataVisualizer`, `PerformanceProfiler`, node data tables, and Chrome trace dumps.

## Route elsewhere

- Pipeline node construction, schemas, `RuntimePipeline.batch()`, `debug()` call options, and `AutoConfig` belong to the sibling pipeline-programming sub-skill.
- Operator registration, Hub operators, and CLI template generation belong to operator-hub-and-cli.
- Service startup, HTTP/GRPC, Docker, and Triton deployment belong to serving-and-triton.
- PyTorch training loops, `NNOperator.train()`, `Trainer`, and model-zoo execution belong to training-and-models.

## Start with these bundled references

1. Read [references/data-structures.md](references/data-structures.md) for `DataCollection`, `Entity`, `DataLoader`, media wrapper APIs, serialization contracts, and safe usage examples.
2. Read [references/visualization-and-profiling.md](references/visualization-and-profiling.md) for visualizer, tracer, and profiler output patterns.
3. Read [references/troubleshooting.md](references/troubleshooting.md) when conversion, display, PIL/numpy, loader, or profiler behavior is surprising.
4. Run [`scripts/data_collection_smoke.py`](scripts/data_collection_smoke.py) in an environment where Towhee is installed to validate the core data utilities without network, model downloads, or GPUs.

## Minimal decision flow

- If the input is a pipeline result queue, wrap it once with `towhee.DataCollection(result)` before accessing rows repeatedly.
- If you need portable/debuggable rows, call `dc.to_dict()` and reconstruct with `DataCollection.from_dict(saved_dict)`.
- If you are feeding many records into a pipeline, prefer `DataLoader` with a parser and, when using `RuntimePipeline.batch`, a positive `batch_size`.
- If the data are media arrays, keep the Towhee wrapper metadata (`mode`, `sample_rate`, `timestamp`, `key_frame`) aligned with the numpy shape and downstream library expectations.
- If the task asks what happened inside a pipeline run, use `debug(..., profiler=True, tracer=True)` and inspect `v.result`, `v.profiler`, and `v.tracer` rather than rebuilding nodes here.
