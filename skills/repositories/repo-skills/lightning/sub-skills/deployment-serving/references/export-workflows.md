# Export Workflows

Use this reference to choose and implement production artifacts from Lightning models. Validate numerical equivalence with representative inputs after every export or optimization step.

## Route Selection

| Goal | Recommended route | Notes |
| --- | --- | --- |
| Batch predictions with Lightning devices/callbacks | `Trainer.predict` | Keep Lightning installed; route distributed strategy issues to `../distributed-accelerators/SKILL.md`. |
| Simple Python service that can import the model class | `load_from_checkpoint` + `model.eval()` | Fastest path; keeps Lightning dependency. |
| Runtime without Lightning dependency | Recreate `torch.nn.Module` and load checkpoint tensors | Requires state-dict key mapping and output equivalence tests. |
| Portable PyTorch graph for optimization | `torch.export.export` | Recommended modern PyTorch capture route when model is exportable. |
| Cross-runtime inference | `LightningModule.to_onnx` or `torch.onnx.export` | Requires `onnx` for export and an ONNX runtime for execution. |
| Legacy PyTorch graph deployment | TorchScript trace/script | Use only when the model is compatible and target runtime expects TorchScript. |
| NVIDIA inference acceleration | TensorRT through PyTorch/ONNX ecosystem | Lightning serving validator currently does not validate TensorRT optimization. |
| Smaller/faster models | pruning or post-training quantization | Validate accuracy and latency on target hardware. |

## `torch.export`

`torch.export` captures a PyTorch model into an `ExportedProgram` suitable for production optimization and cross-platform deployment.

```python
import torch
from torch.export import export

model = LitModel.load_from_checkpoint("best_model.ckpt")
model.eval()
example_input = torch.randn(1, 64)

exported_program = export(model, (example_input,))
torch.export.save(exported_program, "model.pt2")

loaded_program = torch.export.load("model.pt2")
with torch.inference_mode():
    output = loaded_program.module()(example_input)
```

For `predict_step` or other non-`forward` methods, wrap the method:

```python
exported_program = torch.export.export(
    lambda batch, idx: model.predict_step(batch, idx),
    (example_batch, 0),
)
torch.export.save(exported_program, "predict_step.pt2")
```

Checklist:

- Put the model in `eval()` before export.
- Use representative example inputs with correct batch shape and dtype.
- Keep dynamic control flow and Python side effects out of the exported path.
- Load the artifact and compare outputs to eager mode before shipping.

## ONNX

Use ONNX when the deployment runtime is ONNX Runtime or another ONNX-compatible platform.

```python
import torch
from lightning.pytorch import LightningModule

class SimpleModel(LightningModule):
    def __init__(self):
        super().__init__()
        self.layer = torch.nn.Linear(64, 4)
        self.example_input_array = torch.randn(1, 64)

    def forward(self, x):
        return torch.relu(self.layer(x.view(x.size(0), -1)))

model = SimpleModel.load_from_checkpoint("best_model.ckpt")
model.eval()
model.to_onnx("model.onnx", export_params=True)
```

If `example_input_array` is not set, pass `input_sample` explicitly:

```python
input_sample = torch.randn(1, 64)
model.to_onnx("model.onnx", input_sample, export_params=True)
```

Validate with ONNX Runtime when available:

```python
import numpy as np
import onnxruntime

session = onnxruntime.InferenceSession("model.onnx")
input_name = session.get_inputs()[0].name
outputs = session.run(None, {input_name: np.random.randn(1, 64).astype("float32")})
```

Checklist:

- Install optional packages such as `onnx` and `onnxruntime` only when the route requires them.
- Ensure NumPy input dtype matches model expectations, usually `float32`.
- Compare ONNX outputs against eager PyTorch on the same input with an appropriate tolerance.
- If export fails, simplify the exported method or route to `torch.export`/pure PyTorch.

## TorchScript

TorchScript remains useful when a target runtime requires traced or scripted modules. Prefer tracing for stable tensor-only control flow and scripting for compatible control flow.

```python
model = LitModel.load_from_checkpoint("best_model.ckpt")
model.eval()
example_input = torch.randn(1, 64)

traced = torch.jit.trace(model, example_input)
traced.save("model.ts")
loaded = torch.jit.load("model.ts")
```

Checklist:

- Trace only with representative shapes; traces may not generalize through data-dependent control flow.
- Script only code that TorchScript can compile.
- Validate loaded TorchScript outputs against eager outputs.
- Do not assume `ServableModuleValidator(optimization="script")` validates this path; current validator source raises `NotImplementedError` for non-`None` optimization.

## TensorRT

Use TensorRT when the target is NVIDIA inference hardware and the project already has the appropriate CUDA/TensorRT stack. Lightning does not hide TensorRT system requirements.

Practical route:

1. Export a stable ONNX or PyTorch artifact.
2. Convert with the TensorRT toolchain selected by the deployment platform.
3. Validate latency, memory, and numerical tolerance on the target NVIDIA runtime.
4. Keep a CPU or eager-mode smoke check for development machines that do not have TensorRT.

Do not claim TensorRT runtime validation unless it was actually run on compatible hardware and drivers. Current `ServableModuleValidator` signature mentions `optimization="tensorrt"`, but current source raises `NotImplementedError` for all non-`None` optimizations.

## Pruning

Use Lightning's `ModelPruning` callback during training when the production goal is smaller models or faster inference.

```python
from lightning.pytorch import Trainer
from lightning.pytorch.callbacks import ModelPruning

trainer = Trainer(callbacks=[ModelPruning("l1_unstructured", amount=0.5)])
```

Iterative pruning can pass a callable amount:

```python
def pruning_amount(epoch):
    if epoch == 10:
        return 0.5
    if epoch == 50:
        return 0.25
    if 75 < epoch < 99:
        return 0.01
    return 0.0

trainer = Trainer(callbacks=[ModelPruning("l1_unstructured", amount=pruning_amount)])
```

Checklist:

- Use PyTorch pruning method names or custom `torch.nn.utils.prune.BasePruningMethod` subclasses.
- Measure both prediction quality and inference latency after pruning.
- Keep pruning schedule/training mechanics in `../training-core/SKILL.md`; keep production impact and validation here.

## Post-Training Quantization

Lightning documentation points to Intel Neural Compressor for post-training quantization of fine-tuned Lightning/PyTorch models on Intel CPUs/GPUs. Dynamic quantization is usually the simplest starting point; static quantization needs calibration data.

```python
from neural_compressor.config import PostTrainingQuantConfig
from neural_compressor.quantization import fit

conf = PostTrainingQuantConfig(approach="dynamic")
q_model = fit(model=model.model, conf=conf, eval_func=eval_func)
q_model.save("saved_model")
```

Static quantization requires a calibration dataloader:

```python
conf = PostTrainingQuantConfig(approach="static")
q_model = fit(
    model=model.model,
    conf=conf,
    calib_dataloader=calibration_loader,
    eval_func=eval_func,
)
```

Checklist:

- Install and validate `neural-compressor` only when this route is requested.
- Define `eval_func` to return the deployment metric the user cares about.
- Use a representative calibration set for static quantization.
- Compare FP32 vs INT8 accuracy, latency, and memory on target hardware.

## Artifact Validation Checklist

For any export route, create a small validation script that:

1. Loads the original Lightning or PyTorch model in `eval()` mode.
2. Creates fixed representative inputs with deterministic seeds.
3. Runs eager inference under `torch.inference_mode()`.
4. Loads the exported artifact in a fresh object/session.
5. Compares shape, dtype, and numerical values within tolerance.
6. Records unsupported optional dependencies separately from model correctness.

If the task spans checkpoint creation, route the training step to `../training-core/SKILL.md` and return here for artifact packaging and validation.
