# Export Workflows

## Direct `.pte` Export

Use this path when the user has a PyTorch `nn.Module` and representative inputs.

```python
import torch
from executorch.exir import to_edge_transform_and_lower

model = MyModel().eval()
inputs = (torch.randn(1, 3, 224, 224),)
exported = torch.export.export(model, inputs)
et_program = to_edge_transform_and_lower(exported).to_executorch()
with open("model.pte", "wb") as f:
    f.write(et_program.buffer)
```

Add partitioners only after backend requirements are known. For example, XNNPACK CPU delegation uses `XnnpackPartitioner`; QNN and Cortex-M have dedicated sibling sub-skills.

## Dynamic Shapes

Use `torch.export.Dim` bounds for dimensions that vary at runtime. Keep bounds tight because ExecuTorch uses shape bounds for optimization and memory planning.

```python
from torch.export import Dim, export

dynamic_shapes = {"x": {2: Dim("h", min=16, max=1024), 3: Dim("w", min=16, max=1024)}}
exported = export(model.eval(), (example,), dynamic_shapes=dynamic_shapes)
```

## Program-Data Separation

Use program-data separation when weights/constants should live outside the `.pte`. Tag constants before re-exporting and write tensor data to an output directory. Runtime validation then needs a loader that accepts both `.pte` and `.ptd`.

## PT2E Quantization Placement

The common PT2E flow is: choose a backend quantizer, `prepare_pt2e`, calibrate on representative samples, `convert_pt2e`, then export/lower the quantized model. Backend-specific quantizer choices belong to `backend-selection`, `qualcomm`, or `cortex-m`.

## Higher-Level `executorch.export` API

Use the recipe API when the task benefits from explicit staged export configuration:

```python
from executorch.export import export, ExportRecipe, LoweringRecipe

session = export(model, [(example_input,)], export_recipe=ExportRecipe(lowering_recipe=LoweringRecipe()))
```

Verified signatures from inspection included `export(model, example_inputs=None, export_recipe=None, name=None, dynamic_shapes=None, constant_methods=None, artifact_dir=None, generate_etrecord=False)` and recipe dataclasses for quantization/lowering/backend config.

