# YOLOX Export Workflows

This reference covers ONNX and TorchScript export for trained YOLOX checkpoints. Use dry-runs to validate model construction before loading weights or writing artifacts.

## Checkpoint and model selection

A real export needs:

- A checkpoint path that exists.
- Either a built-in `--name` (`yolox-s`, `yolox-m`, `yolox-l`, `yolox-x`, `yolox-tiny`, `yolox-nano`, `yolov3`) or a custom `--exp-file`.
- Matching `num_classes`, depth/width/depthwise settings, and `test_size` between checkpoint and `Exp`.
- Optional trailing `opts` only for existing `Exp` fields.

YOLOX checkpoints usually contain `ckpt["model"]`; raw state dicts are also possible.

## ONNX export

Important flags:

| Flag | Meaning | Notes |
|---|---|---|
| `--output` | Output ONNX file in bundled helper | Official CLI uses `--output-name`; helper uses `--output`. |
| `--input-name`, `--output-name` | ONNX tensor names | Defaults are `images` and `output`. |
| `--opset` | ONNX opset | Default 11; older OpenVINO paths sometimes need 10. |
| `--batch-size` | Dummy input batch | Static unless `--dynamic` is set. |
| `--dynamic` | Dynamic batch axis | Use only when the target runtime supports it. |
| `--simplify` | Run onnx-simplifier | Requires `onnx` and `onnxsim`; disable if simplification fails. |
| `--decode-in-inference` | Export decoded outputs | Leave unset for raw-output deployment paths that decode outside the graph. |

Example:

```bash
python scripts/export_yolox_template.py \
  --format onnx \
  --name yolox-s \
  --checkpoint yolox_s.pth \
  --output yolox_s.onnx \
  --batch-size 1 \
  --opset 11
```

Dynamic/simplified graph:

```bash
python scripts/export_yolox_template.py \
  --format onnx \
  --name yolox-s \
  --checkpoint yolox_s.pth \
  --output yolox_s_dynamic.onnx \
  --dynamic \
  --simplify
```

## TorchScript export

TorchScript export traces the model with a dummy tensor shaped from `exp.test_size` and saves a `.pt` file.

```bash
python scripts/export_yolox_template.py \
  --format torchscript \
  --name yolox-s \
  --checkpoint yolox_s.pth \
  --output yolox_s.torchscript.pt
```

Do not pass ONNX-only flags such as `--dynamic`, `--opset`, or `--simplify` with TorchScript.

## Dry-run before real export

```bash
python scripts/export_yolox_template.py --format onnx --name yolox-s --dry-run
```

Dry-run constructs the experiment/model and reports model selector, experiment name, test size, parameter count, batch size, decode setting, checkpoint existence, output path, ONNX opset, dynamic axes, tensor names, and simplification setting. It does not load weights or write an exported model.

## Source-script treatment

- ONNX and TorchScript export behavior was adapted into `scripts/export_yolox_template.py` because those paths can be made checkout-independent by requiring an explicit checkpoint.
- TensorRT conversion is reference-only because it requires TensorRT, `torch2trt`, a CUDA GPU, and runtime-specific engine artifacts.
- C++/Android/OpenVINO/ncnn/MegEngine/nebullvm demos are not copied; their operational facts are distilled in `deployment-backends.md`.
