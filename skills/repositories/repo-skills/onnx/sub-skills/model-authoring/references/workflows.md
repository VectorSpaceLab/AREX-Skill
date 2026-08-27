# ONNX Model Authoring Workflows

## Build, check, and save a tiny model

```python
import numpy as np
import onnx
from onnx import TensorProto, helper

x = helper.make_tensor_value_info("X", TensorProto.FLOAT, [2])
y = helper.make_tensor_value_info("Y", TensorProto.FLOAT, [2])
bias = onnx.numpy_helper.from_array(np.array([1.0, 2.0], dtype=np.float32), name="B")
node = helper.make_node("Add", ["X", "B"], ["Y"])
graph = helper.make_graph([node], "add-bias", [x], [y], initializer=[bias])
model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 14)])
onnx.checker.check_model(model)
onnx.save_model(model, "add-bias.onnx")
```

Keep graph value names unique within each graph. Graph inputs and outputs need type information; top-level tensor shapes must specify rank even when dimensions are unknown.

## Round-trip formats

Use `format="protobuf"`, `"textproto"`, `"json"`, or the experimental `"onnxtxt"` when a file extension is absent or ambiguous. After each round trip, load the result and run the checker. ONNX text syntax is more restrictive than Python and belongs to the validation/operator-maintenance references.

```python
onnx.save_model(model, "model.json", format="json")
round_trip = onnx.load_model("model.json", format="json")
onnx.checker.check_model(round_trip)
```

## Symbolic dimensions and IO updates

Use `None` for an anonymous unknown dimension and a string such as `"batch"` when the same dimension should be related across values. `onnx.tools.update_model_dims.update_inputs_outputs_dims` mutates input/output shapes and runs model checking; use exact tensor names and preserve rank.

## Compose and extract

Before `merge_models`, inspect both models' input/output names and opset imports. Use `io_map=[("left_output", "right_input")]`; add prefixes when names collide. After merging, validate the combined model. For extraction, `onnx.utils.extract_model` is path-based and exact: give input/output tensor names, not node names. Control-flow subgraphs must not be cut through accidentally.

## External data

For a model with a small initializer, `save_model(..., save_as_external_data=True, all_tensors_to_one_file=True, location="weights.bin", size_threshold=0)` writes a model file and a relative data file. Keep the data file in the model directory or load with `load_external_data=False` followed by `load_external_data_for_model(model, base_dir)`. Do not use `..` paths or untrusted locations.

For models larger than the single-protobuf limit, preserve external data and use path-based checker/shape-inference APIs. `ModelContainer` is intended for large initializers that should not be copied through protobuf while the model is being assembled.

## Safe helper

```bash
python sub-skills/model-authoring/scripts/create_tiny_model.py --output /tmp/onnx-tiny.onnx
python sub-skills/model-authoring/scripts/inspect_model_io.py --model /tmp/onnx-tiny.onnx --infer-shapes
```

The helpers write only the path explicitly supplied by the caller and perform checker validation before reporting success.
