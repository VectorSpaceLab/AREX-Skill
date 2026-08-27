# D-FINE Inference and ONNX Export

This reference distills the D-FINE deployment and inference workflows into copyable command patterns. Native D-FINE commands assume a D-FINE source checkout root with a Python environment able to import D-FINE and any optional backend packages needed for the selected backend. Bundled helper snippets use paths relative to this `references/` directory, such as `../scripts/dfine_inference_command.py`; resolve them through the generated skill tree if running from another working directory.

## Backend input/output contract

| Workflow | Required inputs | Optional inputs | Native command output |
|---|---|---|---|
| PyTorch image inference | config, checkpoint, image path, device | model size/config family | `torch_results.jpg` in the command working directory |
| PyTorch video inference | config, checkpoint, video path, device | model size/config family | `torch_results.mp4` in the command working directory |
| ONNX export | config, checkpoint | ONNX checker, ONNX simplifier | checkpoint basename with `.pth` replaced by `.onnx`; without a checkpoint the script writes `model.onnx` with random weights |
| ONNX Runtime image inference | ONNX model, image path | CPU/GPU provider setup outside the native CLI | `onnx_result.jpg` |
| ONNX Runtime video inference | ONNX model, video path | CPU/GPU provider setup outside the native CLI | `onnx_result.mp4` |
| TensorRT image inference | TensorRT engine, image path, CUDA device | verbose TensorRT engine inspection outside the native CLI | `trt_result.jpg` |
| TensorRT video inference | TensorRT engine, video path, CUDA device | verbose TensorRT engine inspection outside the native CLI | `trt_result.mp4` |
| OpenVINO image inference | OpenVINO IR/XML model, image path | OpenVINO device is `AUTO` in the native CLI | `openvino_result.jpg` |
| EMA extraction | checkpoint containing `ema.module` | explicit output path | a checkpoint with one top-level key: `model` |

## PyTorch inference

Use PyTorch inference when the user has a D-FINE config and a trained `.pth` checkpoint and wants annotated image/video output from the native model.

```bash
python tools/inference/torch_inf.py \
  -c configs/dfine/dfine_hgnetv2_l_coco.yml \
  -r model.pth \
  --input image.jpg \
  --device cuda:0
```

Inputs and behavior:

- `-c/--config`: D-FINE YAML config matching the checkpoint family and class count.
- `-r/--resume`: checkpoint. The native loader uses `checkpoint["ema"]["module"]` when present, otherwise `checkpoint["model"]`.
- `--input`: image extensions `.jpg`, `.jpeg`, `.png`, `.bmp` are treated as images; other extensions are treated as video.
- `--device`: any PyTorch device string accepted by the installed build, commonly `cpu` or `cuda:0`.
- The native script disables `HGNetv2.pretrained` before loading the checkpoint, loads the training-mode state dict, wraps `cfg.model.deploy()` and `cfg.postprocessor.deploy()`, and runs the deployed pair.
- Image preprocessing resizes directly to `640x640` with `torchvision.transforms.Resize((640, 640))` and passes original target size as `[width, height]`.
- Image output is `torch_results.jpg`; video output is `torch_results.mp4`.

Safe command generator:

```bash
python ../scripts/dfine_inference_command.py \
  --backend torch \
  --config configs/dfine/dfine_hgnetv2_l_coco.yml \
  --checkpoint model.pth \
  --input image.jpg \
  --device cuda:0
```

## ONNX export

Use ONNX export when the user wants an ONNX model for ONNX Runtime, TensorRT, OpenVINO conversion, or downstream deployment.

```bash
pip install onnx onnxsim
python tools/deployment/export_onnx.py \
  --check \
  --simplify \
  -c configs/dfine/dfine_hgnetv2_l_coco.yml \
  -r model.pth
```

Export behavior distilled from the native exporter:

- The exporter constructs `YAMLConfig(config, resume=checkpoint)` and sets `HGNetv2.pretrained: false` before model construction.
- If the checkpoint has `ema`, it exports `checkpoint["ema"]["module"]`; otherwise it exports `checkpoint["model"]`.
- It wraps `cfg.model.deploy()` and `cfg.postprocessor.deploy()` so the exported graph returns postprocessed detection outputs.
- Input names are `images` and `orig_target_sizes`; output names are `labels`, `boxes`, and `scores`.
- Export uses ONNX opset 16 and dynamic batch axes for `images` and `orig_target_sizes`.
- The native dummy input is shaped like `32x3x640x640`; large-memory export failures can therefore occur on small machines.
- Output path is derived by replacing `.pth` in the checkpoint filename with `.onnx`. If no checkpoint is supplied, the script writes `model.onnx` with randomly initialized weights; that is only useful for graph smoke testing.
- In the current CLI, `--check` and `--simplify` are default-enabled by the parser, so keep `onnx` and `onnxsim` installed even if the flags are not written explicitly.

Safe export command generator:

```bash
python ../scripts/dfine_export_command.py \
  --config configs/dfine/dfine_hgnetv2_l_coco.yml \
  --checkpoint model.pth
```

## ONNX Runtime inference

Use ONNX Runtime when the user already has an ONNX model and wants annotated image/video output.

```bash
pip install -r tools/inference/requirements.txt
python tools/inference/onnx_inf.py --onnx model.onnx --input image.jpg
```

Inputs and behavior:

- `--onnx`: ONNX model exported with input names `images` and `orig_target_sizes` and output names `labels`, `boxes`, `scores`.
- `--input`: image or video path.
- The native script creates an `onnxruntime.InferenceSession` and prints the available ONNX Runtime device.
- ONNX image/video preprocessing preserves aspect ratio, pads to a square 640 canvas, and then de-pads boxes before drawing on the original image/frame.
- Image output is `onnx_result.jpg`; video output is `onnx_result.mp4`.

Safe command generator:

```bash
python ../scripts/dfine_inference_command.py \
  --backend onnx \
  --onnx model.onnx \
  --input image.jpg
```

## TensorRT inference

Use TensorRT inference when the user already has a TensorRT engine built from a D-FINE ONNX model and a CUDA/TensorRT runtime.

```bash
python tools/inference/trt_inf.py --trt model.engine --input image.jpg --device cuda:0
```

Inputs and behavior:

- `--trt`: serialized TensorRT engine file.
- `--input`: image/video path; image extensions `.jpg`, `.jpeg`, `.png`, `.bmp` are treated as images.
- `--device`: CUDA device string for tensors and engine bindings.
- The engine is expected to expose input tensors compatible with `images` and `orig_target_sizes`; outputs are expected to include `labels`, `boxes`, and `scores`.
- TensorRT image/video preprocessing matches the PyTorch native inference path: direct resize to `640x640`, no aspect-ratio padding, and original target size as `[width, height]`.
- Image output is `trt_result.jpg`; video output is `trt_result.mp4`.

Safe command generator:

```bash
python ../scripts/dfine_inference_command.py \
  --backend trt \
  --trt-engine model.engine \
  --input image.jpg \
  --device cuda:0
```

## OpenVINO inference

Use OpenVINO inference when the user has converted the ONNX model to an OpenVINO IR/XML model and wants image output.

```bash
python tools/inference/openvino_inf.py --ov_model model.xml --image image.jpg
```

Inputs and behavior:

- `--ov_model`: OpenVINO model path, usually the `.xml` IR path with its matching `.bin` file next to it.
- `--image`: image path. The native OpenVINO CLI is image-only.
- The native class compiles the model on `AUTO`, reads available devices from OpenVINO runtime, and uses compiled input shape to determine target size.
- Preprocessing can preserve ratio, scales by `min(target_h / h, target_w / w)`, pads with value `114`, and feeds `images` plus `orig_target_sizes`.
- Output is `openvino_result.jpg`.

Safe command generator:

```bash
python ../scripts/dfine_inference_command.py \
  --backend openvino \
  --openvino-model model.xml \
  --input image.jpg
```

## OpenVINO model conversion from ONNX

D-FINE does not include a dedicated Python conversion wrapper for OpenVINO. For current OpenVINO releases, convert an exported ONNX graph with the OpenVINO converter available in the user's environment, for example:

```bash
ovc model.onnx --output_model model.xml
```

The resulting IR should include a `.xml` file and a sibling `.bin` file. Use the `.xml` path with the native OpenVINO inference command.

## EMA-only checkpoint extraction

Use EMA extraction when a checkpoint has the D-FINE training checkpoint structure and a downstream export or inference path expects a simpler checkpoint whose top-level `model` key is the EMA module state dict.

```bash
python ../scripts/extract_ema_checkpoint.py model.pth
```

Default output is `<checkpoint-stem>_converted<suffix>` next to the input checkpoint. The saved object is exactly:

```python
{"model": checkpoint["ema"]["module"]}
```

This utility does not train, fine-tune, or create new weights; it only repackages existing EMA weights.
