# D-FINE Deployment and Benchmarks

This reference covers deployment conversion, latency/static benchmarks, FiftyOne visualization, and C++ example boundaries. It complements [inference-and-export.md](inference-and-export.md). Bundled helper snippets use paths relative to this `references/` directory, such as `../scripts/dfine_export_command.py`; resolve them through the generated skill tree if running from another working directory.

## Optional backend prerequisites

| Capability | Runtime pieces | Notes |
|---|---|---|
| ONNX export check/simplify | `onnx`, `onnxsim`, PyTorch | Native exporter uses opset 16 and default-enabled check/simplify. |
| ONNX Runtime inference | `onnxruntime`, OpenCV, PIL/torchvision | Native inference creates `onnxruntime.InferenceSession(model.onnx)`. |
| TensorRT engine build | NVIDIA CUDA stack plus the `trtexec` binary | `trtexec` is a command-line tool, not the same thing as the Python `tensorrt` package. |
| TensorRT Python inference | Python `tensorrt`, PyTorch with CUDA, OpenCV | Native image/video inference deserializes a `.engine` file and binds tensors by engine tensor names. |
| TensorRT benchmark | Python `tensorrt`, `pycuda`, PyTorch with CUDA, `tqdm`, image directory | Native benchmark warms up heavily and assumes CUDA. |
| OpenVINO inference | OpenVINO runtime, OpenCV | Native CLI compiles the IR/XML model on `AUTO`. |
| FLOPs/MACs/params | `calflops`, PyTorch | Uses the deployed D-FINE model with input shape `1x3x640x640`; no checkpoint is required. |
| FiftyOne visualization | `fiftyone`, PyTorch/CUDA, checkpoint, COCO validation samples | Native script launches a long-lived app session and writes FiftyOne dataset exports in the working directory. |

## ONNX to TensorRT engine creation

The README deployment flow is:

```bash
python tools/deployment/export_onnx.py --check -c configs/dfine/dfine_hgnetv2_l_coco.yml -r model.pth
trtexec --onnx="model.onnx" --saveEngine="model.engine" --fp16
```

Because D-FINE ONNX export declares dynamic batch axes for both `images` and `orig_target_sizes`, TensorRT engine creation is often more robust with explicit shape profiles:

```bash
trtexec \
  --onnx=model.onnx \
  --saveEngine=model.engine \
  --fp16 \
  --minShapes=images:1x3x640x640,orig_target_sizes:1x2 \
  --optShapes=images:1x3x640x640,orig_target_sizes:1x2 \
  --maxShapes=images:32x3x640x640,orig_target_sizes:32x2
```

Use `scripts/dfine_export_command.py --build-trt` to generate both commands without executing them:

```bash
python ../scripts/dfine_export_command.py \
  --config configs/dfine/dfine_hgnetv2_l_coco.yml \
  --checkpoint model.pth \
  --build-trt \
  --trt-engine model.engine
```

Important engine contract:

- Inputs should be compatible with `images` shaped `N x 3 x 640 x 640` and `orig_target_sizes` shaped `N x 2`.
- Outputs should expose D-FINE postprocessed tensors equivalent to `labels`, `boxes`, and `scores`.
- The engine is CUDA/TensorRT-version-specific; rebuild the engine when TensorRT, CUDA, GPU architecture, ONNX graph, or shape profile changes.

## FLOPs, MACs, and parameter count

Native static benchmark:

```bash
python tools/benchmark/get_info.py -c configs/dfine/dfine_hgnetv2_l_coco.yml
```

Behavior:

- Loads the config with no checkpoint.
- Wraps `cfg.model.deploy()` only, not the postprocessor.
- Calculates FLOPs/MACs for input shape `(1, 3, 640, 640)` with `calflops`.
- Prints `Model FLOPs`, `MACs`, and `Params`.

Safe command generator:

```bash
python ../scripts/dfine_benchmark_command.py \
  --benchmark flops \
  --config configs/dfine/dfine_hgnetv2_l_coco.yml
```

## TensorRT latency benchmark

Native latency benchmark source accepts an image directory and an engine directory:

```bash
python tools/benchmark/trt_benchmark.py --infer_dir val2017 --engine_dir engines
```

Inputs and behavior:

- `--infer_dir`: directory of `.jpg` images used for inference timing.
- `--engine_dir`: directory containing one or more `*.engine` files.
- `--busy`: optional flag that changes latency sample trimming when other processes may be running.
- The script warms up each engine, runs many iterations, and reports latency in milliseconds.
- Dataset preprocessing resizes with max size 640, pads to `640x640` with fill value `114`, converts to tensor, and passes `orig_target_sizes` as `[width, height]`.
- The benchmark requires CUDA, TensorRT Python bindings, PyCUDA, and a compatible serialized engine.

Safe command generator:

```bash
python ../scripts/dfine_benchmark_command.py \
  --benchmark trt \
  --infer-dir val2017 \
  --engine-dir engines
```

Note: some README snippets show a `--COCO_dir` flag for latency, but the inspected benchmark parser accepts `--infer_dir`.

## FiftyOne visualization

Native FiftyOne workflow:

```bash
pip install fiftyone
python tools/visualization/fiftyone_vis.py \
  -c configs/dfine/dfine_hgnetv2_l_coco.yml \
  -r model.pth
```

Behavior and constraints:

- Loads or downloads the COCO validation split through FiftyOne Zoo into the user's working environment.
- Launches a FiftyOne app session and keeps it alive in a loop until interrupted.
- Builds D-FINE from config, disables `HGNetv2.pretrained`, loads `ema.module` when present otherwise `model`, and applies the model to a sampled view.
- Exports `saved_predictions_view` and may reuse previously saved views if they already exist in the working directory.
- The native model class calls `.cuda()`, so a CUDA-capable PyTorch setup is expected unless the script is edited.

Use this as an optional visualization workflow, not as a required inference smoke test.

## C++ inference examples

D-FINE includes C++ examples for ONNX Runtime, TensorRT, and OpenVINO. Treat them as reference-only unless the user explicitly wants a native C++ build:

- ONNX Runtime C++ example requires CMake plus ONNX Runtime development package.
- TensorRT C++ example requires TensorRT headers/libraries, CUDA, and `nvonnxparser`.
- OpenVINO C++ example requires OpenVINO CMake package and a compiled model.

Do not ask future agents to inspect those examples before answering ordinary inference/export questions; use this distilled contract and the bundled command generators first.

## Checkpoint to ONNX to TensorRT latency pipeline

For the common deployment-latency pipeline, gather these inputs:

1. D-FINE config matching the checkpoint.
2. Trained checkpoint, preferably `.pth` so the native exporter derives an `.onnx` filename correctly.
3. Desired ONNX output name or the exporter-derived ONNX filename.
4. Desired TensorRT engine path and shape profile.
5. Image directory for latency benchmark.
6. CUDA/TensorRT version and whether fp16 is acceptable.

Then generate commands in order:

```bash
python ../scripts/dfine_export_command.py \
  --config configs/dfine/dfine_hgnetv2_l_coco.yml \
  --checkpoint model.pth \
  --build-trt \
  --trt-engine model.engine

python ../scripts/dfine_benchmark_command.py \
  --benchmark trt \
  --infer-dir val2017 \
  --engine-dir .
```

The first command prints, but does not execute, the ONNX export and `trtexec` engine build commands. The second command prints, but does not execute, the TensorRT latency command.
