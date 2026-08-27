# Export Compatibility

## Readiness Signals

SMP models are PyTorch modules with repository-level tests for `torch.compile`, `torch.export`, and TorchScript on supported model/encoder combinations. Base segmentation models expose compatibility flags such as `_is_torch_scriptable`, `_is_torch_exportable`, and `_is_torch_compilable`; some decoders or encoders override these when a path is known to be unsupported.

Use the bundled `scripts/check_export_readiness.py` before planning a deployment path. It reports installed versions, optional dependency presence, model flags, and an optional forward-pass check.

## ONNX Export Pattern

ONNX export is an optional deployment path. It requires PyTorch ONNX export support and normally the `onnx` package for model checking; `onnxruntime` is only needed if you want to run the exported graph.

```python
import torch
import segmentation_models_pytorch as smp

model = smp.Unet("resnet34", encoder_weights=None, classes=1).eval()
sample = torch.randn(1, 3, 224, 224)

torch.onnx.export(
    model,
    sample,
    "unet_resnet34.onnx",
    export_params=True,
    opset_version=17,
    do_constant_folding=True,
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={
        "input": {0: "batch_size", 2: "height", 3: "width"},
        "output": {0: "batch_size", 2: "height", 3: "width"},
    },
)
```

Validate the exported graph when `onnx` is installed:

```python
import onnx

onnx_model = onnx.load("unet_resnet34.onnx")
onnx.checker.check_model(onnx_model)
```

For runtime parity, compare outputs with `onnxruntime` on representative image sizes and channel counts. Dynamic height/width can still fail for a specific encoder, operation, opset, or backend.

## TorchScript And Tracing

Prefer `torch.jit.script(model.eval())` when the model and encoder are marked scriptable. If scripting fails for a specific encoder/decoder, try tracing with representative inputs only when the model path is shape-stable enough for the deployment target.

SMP's forward path skips the standard input-divisibility check while scripting or tracing. Do not use that as permission to feed invalid image sizes at runtime; preserve the model's stride/divisibility requirements in pre- and post-processing.

## torch.export

`torch.export.export(model, args=(sample,), strict=True)` is covered by SMP tests for supported combinations. Use static representative inputs first, then add dynamic-shape requirements only after the simple export passes.

```python
exported = torch.export.export(model.eval(), args=(sample,), strict=True)
exported_output = exported.module().forward(sample)
```

Compare shape and numeric closeness against eager PyTorch before shipping.

## torch.compile

SMP tests use `torch.compile(model, fullgraph=True, dynamic=True, backend="eager")` for supported combinations. Other backends, especially accelerator-specific ones, can fail because of the Torch version, backend compiler, CUDA stack, or encoder implementation.

```python
compiled = torch.compile(model.eval(), fullgraph=True, dynamic=True, backend="eager")
with torch.inference_mode():
    compiled(sample)
```

If `fullgraph=True` fails, decide whether partial graph compilation is acceptable for the deployment target. Do not claim compile readiness from a single backend unless that backend is the actual production backend.

## Encoder And Architecture Caveats

- Some encoders have explicit script/compile/export limitations; choose the encoder with deployment constraints in mind.
- Some transformer-style models and decoders are less friendly to scripting or dynamic shape export than common convolutional backbones.
- Some models require input height and width divisible by the encoder output stride during eager inference.
- Pretrained encoder downloads are unrelated to export capability; use `encoder_weights=None` for offline export tests.
