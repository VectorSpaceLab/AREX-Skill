# ONNX Validation and Conversion Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `TypeError: infer_shapes only accepts ModelProto or bytes` | A file path was passed to `infer_shapes` | Use `onnx.shape_inference.infer_shapes_path(path)` instead. |
| `ValidationError` points to SSA, topological order, or missing inputs | The graph itself is invalid rather than the serializer | Inspect the model with `model.graph.input`, `initializer`, `node`, and `output` names; fix the graph before retrying conversion or inference. |
| `ValidationError` only appears after `full_check=True` | The model may be structurally legal but shape-inconsistent | Treat that as a real issue in the model or the selected op schema; add or correct value info and rerun. |
| `ParseError` on compact ONNX text | The syntax is not protobuf text and is stricter about graph/function-body grammar | Use parser-oriented fixtures and the ONNX text syntax reference; double-check attribute placement and subgraph bodies. |
| `ConvertError` or a runtime conversion exception | No supported adapter path exists for the requested version/domain pair | Keep the original opset or add a dedicated maintainer task for the missing adapter. |
| Output model from inlining or conversion now fails checker | Expansion or version conversion exposed hidden schema/name problems | Re-run checker and shape inference, then inspect the expanded node list and value names. |
| `check-model` works on a path but not on a model object | The model may exceed in-memory protobuf limits or external data may not be loaded | Prefer path-based validation for large models and keep external data beside the file. |
