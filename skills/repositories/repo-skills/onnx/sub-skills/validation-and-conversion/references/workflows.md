# ONNX Validation and Conversion Workflows

## Validate a saved model

```python
import onnx

model = onnx.load_model("model.onnx")
onnx.checker.check_model(model)
```

For large models, prefer `onnx.checker.check_model("model.onnx")` directly.

## Validate a single node

```python
import onnx
from onnx import helper

node = helper.make_node("Relu", ["X"], ["Y"])
onnx.checker.check_node(node)
```

## Infer shapes after editing a model

```python
import onnx

model = onnx.load_model("model.onnx")
inferred = onnx.shape_inference.infer_shapes(model, strict_mode=True)
onnx.checker.check_model(inferred)
```

Use strict mode when you want a failure instead of a partial result. Use `data_prop=True` only when the selected operators support the extra data-propagation path you need.

## Parse and print compact ONNX text

```python
import onnx

model_text = """
<ir_version: 7, opset_import: ["" : 14]>
g (float[2] X) => (float[2] Y) {
  Y = Relu(X)
}
"""
model = onnx.parser.parse_model(model_text)
print(onnx.printer.to_text(model))
```

## Convert opsets

```python
import onnx

model = onnx.load_model("model.onnx")
converted = onnx.version_converter.convert_version(model, 14)
```

If conversion fails, the model may use a custom domain, an unsupported adapter, or an incompatible source/target path. Keep the original version and document the gap instead of forcing a lossy workaround.

## Inline local functions

```python
import onnx

model = onnx.load_model("model_with_functions.onnx")
inlined = onnx.inliner.inline_local_functions(model)
onnx.checker.check_model(inlined)
```

Use `inline_selected_functions` when only part of a model should be expanded. Re-check the inlined model because function expansion can reveal naming or shape issues that were hidden before inlining.

## Script helper

```bash
python sub-skills/validation-and-conversion/scripts/validate_convert_model.py --help
python sub-skills/validation-and-conversion/scripts/validate_convert_model.py --model /tmp/model.onnx --infer-shapes --print-text
```
