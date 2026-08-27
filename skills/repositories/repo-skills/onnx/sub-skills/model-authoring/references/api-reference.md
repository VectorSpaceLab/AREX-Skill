# ONNX Model Authoring API Reference

Use this reference for parameter-level decisions. The signatures were checked against ONNX 1.23.0 runtime facts.

## Construction

```python
from onnx import TensorProto, helper

x = helper.make_tensor_value_info("X", TensorProto.FLOAT, [None, 3])
y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [None, 3])
node = helper.make_node("Relu", ["X"], ["Y"])
graph = helper.make_graph([node], "relu", [x], [y])
model = helper.make_model(
    graph,
    producer_name="my-tool",
    opset_imports=[helper.make_opsetid("", 14)],
)
```

Important verified signatures:

- `helper.make_node(op_type, inputs, outputs, name=None, doc_string=None, domain=None, overload=None, **kwargs)`; operator attributes are keyword arguments.
- `helper.make_graph(nodes, name, inputs, outputs, initializer=None, doc_string=None, value_info=None, sparse_initializer=None)`.
- `helper.make_model(graph, **kwargs)`; pass metadata, producer fields, and `opset_imports` through keyword arguments.
- `helper.make_tensor_value_info(name, elem_type, shape, doc_string='', shape_denotation=None)`; `None` in a shape entry means an anonymous dynamic dimension, while a string carries a symbolic `dim_param`.
- `helper.make_tensor(name, data_type, dims, vals, raw=False)`; use `numpy_helper.from_array(array, name=None)` for NumPy arrays.
- `helper.make_attribute(key, value, doc_string=None, attr_type=None)`.

## IO and Serialization

- `onnx.load_model(f, format=None, load_external_data=True)` accepts a path-like or readable binary object. `onnx.load` is the compatibility alias.
- `onnx.load_from_string(s, format='protobuf')` loads bytes or text using a selected format.
- `onnx.save_model(proto, f, format=None, *, save_as_external_data=False, all_tensors_to_one_file=True, location=None, size_threshold=1024, convert_attribute=False)` writes a model and optionally externalizes tensors. `onnx.save` is the compatibility alias.
- `onnx.save_tensor` and `onnx.load_tensor` operate on `TensorProto` values.
- Supported built-in formats are `protobuf`, `textproto`, `json`, and experimental `onnxtxt`; extensions can infer the format for path-based IO.

## Transformations

- `onnx.compose.merge_models(m1, m2, io_map, inputs=None, outputs=None, prefix1=None, prefix2=None, name=None, doc_string=None, producer_name='onnx.compose.merge_models', producer_version='1.0', domain='', model_version=1)` connects output/input names across two models.
- `onnx.compose.add_prefix(model, prefix, rename_nodes=True, rename_edges=True, rename_inputs=True, rename_outputs=True, rename_initializers=True, rename_value_infos=True, rename_functions=True, inplace=False)` avoids name collisions; prefer `inplace=False` while debugging.
- `onnx.compose.expand_out_dim(model, dim_idx, inplace=False)` inserts a size-one dimension on model outputs.
- `onnx.utils.extract_model(input_path, output_path, input_names, output_names, check_model=True, infer_shapes=True)` is path-based and extracts a sub-model between exact tensor names.
- `onnx.tools.update_model_dims.update_inputs_outputs_dims(model, input_dims, output_dims)` accepts dictionaries mapping names to lists of integer/symbolic dimensions and checks the result.
- `onnx.tools.replace_constants.replace_initializer_by_constant_of_shape(onx, threshold=128, ir_version=None, use_range=False, value_constant_of_shape=0.5)` reduces large initializer or Constant payloads in a `ModelProto`, `GraphProto`, or `FunctionProto` by replacing them with generated shape/constant nodes for lightweight test fixtures. Validate the transformed model and watch opset constraints when using `Range` or `ConstantOfShape`.

## External and Large Data

- `external_data_helper.convert_model_to_external_data(model, all_tensors_to_one_file=True, location=None, size_threshold=1024, convert_attribute=False)` mutates tensor metadata; save afterward.
- `external_data_helper.load_external_data_for_model(model, base_dir)` resolves external tensor locations from a supplied directory.
- `external_data_helper.convert_model_from_external_data(model)` moves loaded external tensor content back into the model when feasible.
- `ModelContainer`/`make_large_model` keep large initializers outside the serialized protobuf until `save()` is called. Use them for deliberately large model workflows, not ordinary tiny fixtures.
