# ONNX Validation and Conversion API Reference

## Checker

- `onnx.checker.check_model(model, full_check=False, skip_opset_compatibility_check=False, check_custom_domain=False)` validates a `ModelProto`, path, or serialized bytes.
- `onnx.checker.check_node(node)` validates a `NodeProto`.
- `onnx.checker.check_graph(graph)` and `onnx.checker.check_tensor(tensor)` are available when a smaller target is more useful.
- `onnx.checker.ValidationError` is the standard exception class for legality failures.

Use `check_model(path)` for very large models or when external data is stored beside the file. Use `full_check=True` only when you need the extra shape-consistency pass.

## Shape inference

- `onnx.shape_inference.infer_shapes(model, check_type=False, strict_mode=False, data_prop=False)` accepts a `ModelProto` or bytes and returns a model with inferred `value_info`.
- `onnx.shape_inference.infer_shapes_path(model_path, output_path='', check_type=False, strict_mode=False, data_prop=False)` is the path-based form.
- `onnx.shape_inference.infer_node_outputs(schema, node, input_types, input_data=None, input_sparse_data=None, opset_imports=None, ir_version=IR_VERSION)` is a lower-level helper for op-schema work.
- `onnx.shape_inference.infer_function_output_types(function, input_types, attributes)` computes function output types.
- `onnx.shape_inference.InferenceError` reports inference failures.

`infer_shapes` is not a path API. Use `infer_shapes_path` when the caller provides file paths or when the model is too large to keep in memory comfortably.

## Parser and printer

- `onnx.parser.parse_model(text)` parses a full ONNX model in compact text form.
- `onnx.parser.parse_graph(text)`, `parse_function(text)`, and `parse_node(text)` parse smaller artifacts.
- `onnx.printer.to_text(proto)` renders a model/function/graph/node back to compact text.
- `onnx.parser.ParseError` signals grammar or syntax problems.

The compact syntax is not protobuf text format. Use the grammar-oriented examples in the workflow reference when authoring function bodies or parser fixtures.

## Version conversion and inlining

- `onnx.version_converter.convert_version(model, target_version)` converts a `ModelProto` in the default domain.
- `onnx.version_converter.ConvertError` indicates that a supported adapter path was not available.
- `onnx.inliner.inline_local_functions(model, convert_version=False)` expands local functions.
- `onnx.inliner.inline_selected_functions(model, function_ids, exclude=False, inline_schema_functions=False)` inlines a chosen subset.

Converted or inlined models should be revalidated with checker and, when relevant, shape inference.
