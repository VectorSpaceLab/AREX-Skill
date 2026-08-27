# Backend Export Patterns

## XNNPACK CPU Delegate

```python
from executorch.backends.xnnpack.partition.xnnpack_partitioner import XnnpackPartitioner
from executorch.exir import to_edge_transform_and_lower

edge = to_edge_transform_and_lower(exported_program, partitioner=[XnnpackPartitioner()])
program = edge.to_executorch()
```

Use XNNPACK as the first performance-oriented backend for general mobile CPU targets and as fallback for mixed-backend strategies.

## Multiple Partitioners

When two backends can cover different graph regions, provide partitioners in priority order. Verify unsupported ops fall back deliberately rather than silently.

## Backend-Specific Quantization

Quantization is backend-specific. The common PT2E flow is consistent, but the quantizer object and supported dtype/granularity differ. Validate quantized PyTorch accuracy before lowering.

## Build Flags and Runtime Libraries

Backend export is not enough; runtime loading on a device requires the matching backend libraries to be built and linked. Keep export-time partitioner availability separate from runtime target availability.

## Routing to Deep Backends

- QNN/Qualcomm: route to `../qualcomm/SKILL.md` for compile specs, SDK/device arguments, model enablement, and intermediate-output debugging.
- Cortex-M/CMSIS-NN: route to `../cortex-m/SKILL.md` for PT2E quantizer/pass manager and dialect/implementation tests.
- LLM backend runners: route to `../llm-workflows/SKILL.md` after selecting backend.

