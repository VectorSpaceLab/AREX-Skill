# ONNX Model Authoring Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValidationError` reports duplicate output names or undefined values | Graph violates SSA or a node references a name not defined by an input, initializer, or earlier node | Print all graph inputs/initializers/node outputs, rename collisions, topologically sort nodes, and re-run `checker.check_model`. |
| Model is rejected because an input/output has no type or rank | Top-level `ValueInfoProto` is incomplete | Build IO with `helper.make_tensor_value_info`; use `None` or a symbolic string for unknown dimensions, but preserve rank. |
| `helper.make_node` accepts an attribute but the checker rejects it | Attribute name/type/default does not match the selected opset schema | Confirm the operator's domain/opset and attribute spelling; use `validation-and-conversion` to inspect schema/version behavior. |
| Save/load round trip uses the wrong format | Extension did not infer the intended serializer or a file-like object has no extension | Pass `format=` explicitly and use a supported format. Always validate after reloading. |
| External tensor file is missing or ignored | Relative location is resolved from the model directory, not the process working directory | Keep data beside the model or pass the correct `base_dir` to `load_external_data_for_model`; do not use `..` paths. |
| `check_model(model)` fails for a very large model | Serializing the in-memory model crosses the single-protobuf limit | Use `checker.check_model(model_path)` and `shape_inference.infer_shapes_path`; preserve external data. |
| `compose.merge_models` reports incompatible opsets or names | Models import different versions/domains or the IO map uses node names instead of tensor names | Inspect `model.opset_import`, graph inputs/outputs, and exact value names; convert or prefix deliberately before merging. |
| `numpy_helper.to_array` gives unexpected dtype/shape | Tensor element type, packed sub-byte format, endianness, or external-data base directory is wrong | Inspect `TensorProto.data_type`, `dims`, `data_location`, and external metadata; use ONNX helpers for dtype conversion rather than guessing NumPy casts. |
