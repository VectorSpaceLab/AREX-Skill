# Model Loading and Runtime Format Reference

## When to read

Read this when choosing how to load RVM for PyTorch, TorchHub, TorchScript,
ONNX, TensorFlow, TensorFlow.js, or CoreML inference.

## PyTorch source-checkout loading

For an explicit checkpoint file:

```python
import torch
from model import MattingNetwork

model = MattingNetwork("mobilenetv3").eval().to("cuda")
model.load_state_dict(torch.load("rvm_mobilenetv3.pth", map_location="cuda"))
```

Use `"resnet50"` for the larger variant and load the matching checkpoint. The
repository does not provide Python package metadata in this snapshot, so the
source checkout must be importable as `model` and `inference` unless the user is
using TorchHub.

## TorchHub

TorchHub exposes:

```python
model = torch.hub.load("PeterL1n/RobustVideoMatting", "mobilenetv3")
model = torch.hub.load("PeterL1n/RobustVideoMatting", "resnet50")
convert_video = torch.hub.load("PeterL1n/RobustVideoMatting", "converter")
```

Default TorchHub model factories load official pretrained weights from release
URLs, so network/cache behavior matters. For offline API smoke tests from a
source checkout, `hubconf.mobilenetv3(pretrained=False)` avoids weight download.

## TorchScript

Load a TorchScript artifact with:

```python
import torch
model = torch.jit.load("rvm_mobilenetv3_fp32.torchscript")
model = torch.jit.freeze(model)  # optional optimization after eval/freeze-compatible load
```

The call contract is the same as the PyTorch model. When passing a frozen model
to `convert_video`, supply `device` and `dtype` explicitly because the converter
may not be able to inspect parameters from a frozen module.

## ONNX

Official ONNX artifacts use opset 12 and the following I/O names.

Inputs:

- `src`: RGB input frame `[B,C,H,W]`, normalized `0..1`, dtype matching the
  model precision.
- `r1i`, `r2i`, `r3i`, `r4i`: recurrent state inputs. Initial states are zero
  tensors shaped `[1,1,1,1]` with dtype matching the model precision.
- `downsample_ratio`: tensor shaped `[1]`, always FP32.

Outputs:

- `fgr`, `pha`, `r1o`, `r2o`, `r3o`, `r4o`.

Naive ONNX Runtime loop:

```python
import numpy as np
import onnxruntime as ort

sess = ort.InferenceSession("rvm_mobilenetv3_fp32.onnx")
rec = [np.zeros([1, 1, 1, 1], dtype=np.float32)] * 4
downsample_ratio = np.array([0.25], dtype=np.float32)

for src in frames:  # [B,C,H,W]
    fgr, pha, *rec = sess.run([], {
        "src": src,
        "r1i": rec[0],
        "r2i": rec[1],
        "r3i": rec[2],
        "r4i": rec[3],
        "downsample_ratio": downsample_ratio,
    })
```

With CUDA ONNX Runtime, IO binding can keep recurrent states on GPU and reduce
transfer overhead.

## TensorFlow SavedModel

TensorFlow models use channel-last input:

```python
import tensorflow as tf

model = tf.keras.models.load_model("rvm_mobilenetv3_tf")
model = tf.function(model)
rec = [tf.constant(0.)] * 4
downsample_ratio = tf.constant(0.25)

for src in frames:  # [B,H,W,C]
    out = model([src, *rec, downsample_ratio])
    fgr, pha = out["fgr"], out["pha"]
    rec = [out["r1o"], out["r2o"], out["r3o"], out["r4o"]]
```

Do not feed PyTorch channel-first tensors into the TensorFlow model without
transposing.

## TensorFlow.js

The repository's docs point to a TF.js starter implementation on a separate
branch. Treat TF.js as a web runtime workflow: confirm model artifact paths,
input tensor layout, and recurrent-state recycling in that starter before
writing production code.

## CoreML

CoreML artifacts have fixed resolutions. The first frame omits recurrent state
inputs; CoreML internally creates initial zero states. Subsequent frames pass
`r1i` through `r4i` from the prior outputs.

```python
import coremltools as ct

model = ct.models.model.MLModel("rvm_mobilenetv3_1920x1080_s0.25_int8.mlmodel")
r1 = r2 = r3 = r4 = None

for src in pil_frames:
    if r1 is None:
        inputs = {"src": src}
    else:
        inputs = {"src": src, "r1i": r1, "r2i": r2, "r3i": r3, "r4i": r4}
    outputs = model.predict(inputs)
    fgr, pha = outputs["fgr"], outputs["pha"]
    r1, r2, r3, r4 = outputs["r1o"], outputs["r2o"], outputs["r3o"], outputs["r4o"]
```

If the target resolution differs from the fixed artifact, export a new model or
resize inputs explicitly with the expected trade-off.

## Release format reminders

Official release artifacts include PyTorch `.pth`, TorchScript FP32/FP16,
ONNX FP32/FP16, TensorFlow SavedModel ZIPs, TF.js int8 ZIP, and fixed-resolution
CoreML FP16/int8 `.mlmodel` files for MobileNetV3 and/or ResNet50 variants.
Prefer explicit local artifact paths in automation; downloads are network side
effects and should not be hidden inside generated helper scripts.
