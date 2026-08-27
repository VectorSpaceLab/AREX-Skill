# D-FINE Inference/Export Troubleshooting

Use this page when an inference, export, backend, benchmark, visualization, or EMA extraction workflow fails.

## Missing checkpoint, wrong checkpoint, or missing keys

Symptoms:

- `FileNotFoundError` for a checkpoint path.
- `KeyError: 'ema'`, `KeyError: 'module'`, or `KeyError: 'model'`.
- `RuntimeError` from `load_state_dict` about missing or unexpected keys.

Actions:

1. Confirm the checkpoint path exists and is readable from the command working directory.
2. Confirm the checkpoint matches the selected D-FINE config family and class count.
3. D-FINE inference/export loaders use `checkpoint["ema"]["module"]` when `ema` exists, otherwise `checkpoint["model"]`.
4. `scripts/extract_ema_checkpoint.py` requires exactly the EMA path `ema.module` and saves a new checkpoint whose only required top-level key is `model`.
5. If the checkpoint was created for a different number of classes, route class-count and fine-tuning questions to the training/evaluation and data/config sub-skills rather than forcing inference/export.

## `HGNetv2.pretrained` during loading/export

Symptoms:

- The model tries to download or load backbone pretrained weights while inference/export is supposed to use a checkpoint.
- Export or model construction fails before checkpoint loading because a pretrained path is unavailable.

Actions:

- The native PyTorch inference, ONNX export, and FiftyOne scripts set `HGNetv2.pretrained` to `False` before loading checkpoint weights.
- If writing a custom wrapper, preserve that behavior: disable HGNetv2 pretrained loading before constructing/loading for inference or export.
- If the user only wants architecture inspection without checkpoint loading, route to the architecture/API sub-skill and keep pretrained disabled for smoke checks.

## ONNX export check/simplify failures

Symptoms:

- Missing `onnx` or `onnxsim` imports.
- `onnx.checker.check_model` fails.
- Simplification fails or produces an invalid model.
- TensorRT/OpenVINO cannot consume the exported graph.

Actions:

1. Install the export dependencies for the current environment: `onnx` and `onnxsim`.
2. Remember that the native exporter uses ONNX opset 16, input names `images` and `orig_target_sizes`, output names `labels`, `boxes`, `scores`, and dynamic batch axes.
3. The native parser default-enables check and simplify, so missing `onnxsim` can break export even if the user did not explicitly request simplification.
4. If simplification is the only failing step, first verify whether the raw export was written; the native CLI does not expose a `--no-simplify` flag, so disabling simplification requires editing or wrapping the source script.
5. For downstream TensorRT, pass explicit dynamic-shape profiles for both `images` and `orig_target_sizes`.
6. For downstream OpenVINO, convert the checked ONNX with the user's installed OpenVINO converter and keep the generated XML/BIN pair together.

## TensorRT package, `trtexec`, CUDA, and engine inputs

Symptoms:

- `trtexec: command not found`.
- `ModuleNotFoundError: No module named 'tensorrt'` or `pycuda`.
- Engine deserialization fails.
- Tensor names, shapes, or dtypes do not match `images` and `orig_target_sizes`.
- CUDA device errors or `torch.cuda.is_available()` is false.

Actions:

1. Distinguish the TensorRT command-line binary from Python bindings: engine build uses `trtexec`; native Python inference/benchmark uses the Python `tensorrt` package, and latency benchmark also uses `pycuda`.
2. Rebuild the engine when TensorRT/CUDA/GPU architecture, ONNX graph, fp16/fp32 mode, or shape profiles change.
3. For dynamic-batch ONNX, use shape profiles such as `images:1x3x640x640` and `orig_target_sizes:1x2` for min/opt, and a chosen max batch for max shapes.
4. Confirm the serialized engine exposes compatible input names and postprocessed output names. D-FINE native TensorRT inference expects outputs addressable as `labels`, `boxes`, and `scores`.
5. Use a CUDA device string such as `cuda:0` for native TensorRT inference. TensorRT CPU-only execution is not a substitute.
6. For latency benchmarking, pass an image directory to `--infer_dir` and a directory containing `*.engine` files to `--engine_dir`.

## OpenVINO XML/IR and device availability

Symptoms:

- OpenVINO cannot read the model path.
- `.xml` exists but `.bin` is missing.
- Device `AUTO` cannot compile the model.
- Output image is blank or boxes are malformed.

Actions:

1. Use the OpenVINO IR/XML model path, usually `model.xml`, with its matching `.bin` file in the same directory.
2. Convert from ONNX with the user's OpenVINO converter, for example `ovc model.onnx --output_model model.xml`.
3. The native OpenVINO CLI compiles on `AUTO` and does not expose a device flag; if a specific device is required, edit or wrap the script to pass that device to the `OvInfer` constructor.
4. Confirm the compiled model has inputs compatible with `images` and `orig_target_sizes` and outputs named `labels`, `boxes`, and `scores`.
5. The native OpenVINO path is image-only and writes `openvino_result.jpg`.

## Image/video preprocessing differences and shifted boxes

Symptoms:

- ONNX boxes are shifted compared with PyTorch or TensorRT.
- TensorRT latency numbers look inconsistent with visual inference.
- Outputs are written, but boxes are offset after aspect-ratio changes.

Key difference:

- PyTorch inference and TensorRT inference resize directly to `640x640` without aspect-ratio padding, while passing original `[width, height]` to the postprocessor.
- ONNX Runtime inference preserves aspect ratio, pads to a square 640 canvas, then adjusts boxes by subtracting pad and dividing by scale.
- TensorRT benchmark uses a third preprocessing style: resize with max size near 640, pad to `640x640` with fill value `114`, and pass original target sizes.
- OpenVINO inference also uses keep-ratio padding when `process_image(..., True)` is used.

Actions:

1. When comparing backends, run the same image through each backend and record the exact preprocessing path.
2. Check whether the ONNX model was exported with postprocessing included; the native exporter includes the deploy postprocessor and should output labels/boxes/scores.
3. If ONNX boxes are shifted, inspect the padding offsets and the `orig_target_sizes` value used in the ONNX input feed. The native ONNX script sends the resized padded image dimensions, then manually de-pads boxes.
4. For TensorRT, confirm the engine was built from the same ONNX graph and shape profile expected by the inference script.
5. Do not assume a visualization mismatch means the checkpoint is bad until preprocessing has been aligned.

## Output filename confusion

Actual native output filenames are fixed by script:

| Backend | Image output | Video output |
|---|---|---|
| PyTorch | `torch_results.jpg` | `torch_results.mp4` |
| ONNX Runtime | `onnx_result.jpg` | `onnx_result.mp4` |
| TensorRT | `trt_result.jpg` | `trt_result.mp4` |
| OpenVINO | `openvino_result.jpg` | image-only native CLI |

Some print messages use generic names such as `result.jpg` or `result.mp4`; trust the filenames above when looking for outputs.

## Checkpoint to ONNX to TensorRT latency pipeline

If a user asks for the full deployment-latency pipeline and it fails, debug in this order:

1. Config/checkpoint compatibility: make sure the `.pth` checkpoint loads with the selected config and has `ema.module` or `model`.
2. ONNX export: verify opset 16 export, checker, simplifier, and output filename.
3. TensorRT build: verify `trtexec` exists, CUDA/TensorRT versions match, and dynamic shape profiles include both inputs.
4. Engine inference: run a single TensorRT image command before latency benchmarking.
5. Latency benchmark: provide `--infer_dir` with real `.jpg` images and `--engine_dir` containing the engine.

Use the command generators to print each step before executing anything.

## FiftyOne visualization issues

Symptoms:

- The process launches a UI and appears to hang.
- CUDA errors occur immediately.
- Existing saved views are reused unexpectedly.

Actions:

- The native script intentionally keeps the FiftyOne session alive; interrupt it when done.
- It calls `.cuda()` in the custom model, so expect a CUDA-capable environment unless the script is adapted.
- Remove or rename previous `saved_predictions_view` / `saved_filtered_view` outputs if the user wants a fresh visualization run.
