# Cortex-M API Reference

## Key Objects

| Object | Purpose |
| --- | --- |
| `CortexMQuantizer` | PT2E quantizer for CMSIS-NN-oriented quantized graphs. Convolutions use per-channel int8 config; elementwise ops use a per-tensor config by default. |
| `CortexMPassManager` | Applies Cortex-M pass list to rewrite quantized ATen patterns into `cortex_m::` custom ops. |
| `cortex_m_edge_compile_config()` | Backend compile config used so relevant quantized ops survive lowering before Cortex-M rewrites. |
| `CortexMTester` | Test harness that chains quantize/export/to_edge/run_passes/to_executorch and exposes dialect vs implementation validation. |

## Conceptual Pipeline

```python
quantizer = CortexMQuantizer()
prepared = prepare_pt2e(torch.export.export(model, inputs).module(), quantizer)
# calibrate prepared(*inputs)
quantized = convert_pt2e(prepared)
exported = torch.export.export(quantized, inputs)
edge = to_edge_transform_and_lower(exported, compile_config=cortex_m_edge_compile_config())
edge._edge_programs["forward"] = CortexMPassManager(edge.exported_program(), CortexMPassManager.pass_list).transform()
et_program = edge.to_executorch()
```

Use actual repo/test helper APIs when editing the source tree; the snippet is a distilled mental model for routing and troubleshooting.

