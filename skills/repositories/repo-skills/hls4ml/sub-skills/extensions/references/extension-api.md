# Extension API

This reference covers the minimum set of hooks needed to add a custom layer or backend behavior without changing ordinary conversion paths.

## Extension surfaces

| Surface | Register with | Handler contract | Notes |
| --- | --- | --- | --- |
| Keras v2 layer parser | `register_keras_v2_layer_handler(name, handler)` | The live converter currently calls `handler(keras_layer, input_names, input_shapes, data_reader)` and expects `(layer_dict, output_shape)`. | `layer_dict['class_name']` must match a registered IR layer class. Older docstrings mention a fifth config argument, but the live call is four arguments. |
| Keras v3 layer handler | Subclass `KerasV3LayerHandler` and set `handles` | `handle(layer, in_tensors, out_tensors)` returns one dict or a tuple of dicts. | The metaclass registers handlers automatically when the class is imported. |
| PyTorch layer parser | `register_pytorch_layer_handler(name, handler)` | The converter calls `handler(operation, layer_name, input_names, input_shapes, node, class_object, data_reader, config)`. | Custom modules should normally subclass `HLS4MLModule` so FX treats them as leaf modules. |
| ONNX layer parser | `register_onnx_layer_handler(name, handler)` | The converter calls `handler(node, input_names, input_shapes, onnx_graph)`. | Return a single layer dict and output shape. |
| IR layer class | `register_layer(name, clazz)` | Subclass `Layer`, define `_expected_attributes`, implement `initialize()`. | The parser output `class_name` must match the registry key. |
| Backend templates | `backend.register_template(template_cls)` | Subclass `LayerConfigTemplate` or `FunctionCallTemplate`. | Templates are registered like optimizer passes and populate `config_cpp` or `function_cpp`. |
| Backend source | `backend.register_source(source_file, destination_dir='nnet_utils')` | Provide an absolute source path. | The source is copied into the generated project under the destination directory with its basename. |
| Optimizer pass | `backend.register_pass(name, opt_cls, flow=...)` | Subclass `OptimizerPass` or use the optimizer decorators. | A pass that is not added to a flow will not run. |

## Custom layer building blocks

A minimal custom layer usually needs all of the following:

1. A user-side layer or module class with stable serialization or configuration output.
2. A matching hls4ml IR layer subclass.
3. A parser or handler that maps the frontend object into the IR layer attributes.
4. One or more backend templates that generate the C++ config and function call text.
5. A backend source file that implements the HLS function.
6. If needed, a backend-specific optimizer pass and a flow entry that can reach it.
7. A focused test that proves registration and a small compile/predict smoke.

## IR layer checklist

When you create a new `Layer` subclass, keep these points in mind:

- Use `_expected_attributes` to declare required inputs, weights, type attributes, and configurable attributes.
- Prefer the attribute helpers `Attribute`, `ConfigurableAttribute`, `TypeAttribute`, `WeightAttribute`, and `ChoiceAttribute`.
- Implement `initialize()` to create the output variable with `add_output_variable()` and any weights with `add_weights()` or `add_bias()`.
- If the layer stores precision-like attributes, the layer initialization path will wrap them into `NamedType` objects when needed.
- Avoid reserved names such as `input` for layer names.

## Flow wiring

Optimizer passes are only useful when a flow can reach them.

- `register_flow(name, optimizers, requires=...)` creates a named flow.
- `update_flow(flow_name, add_optimizers=..., remove_optimizers=...)` edits an existing flow.
- `ModelGraph.apply_flow(flow_name, reapply=...)` runs a flow and its dependencies.
- Backend-specific pass names and flow names are namespaced with the backend prefix.
- If you register a pass on a backend, add it to a flow that is reachable from that backend's default flow.

## Practical registration sequence

For a new backend-aware extension, the usual sequence is:

1. Register the frontend parser or handler.
2. Register the IR layer class.
3. Register backend templates.
4. Register the backend source file.
5. Register any optimizer pass and attach it to the correct flow.
6. Verify the custom layer appears in the converted graph and that the pass is actually applied.

## Test target

A good extension test should prove at least one of these outcomes:

- the custom layer is visible in the supported-layer registry,
- the converted model contains the custom IR layer,
- the registered optimizer pass appears in the applied flow record,
- the generated model compiles and matches a tiny reference output.
