# Deployment troubleshooting

Use this reference when a DCNv3 build, ONNX export, TensorRT conversion, or mmdeploy deploy command is requested or failing. Start with safe probes and command-template generation; do not launch compilers, downloads, or real exports until prerequisites and user approval are explicit.

## Quick safe probes

```bash
python -V
python -c "import sys; print(sys.executable)"
python -c "import torch; print('torch', torch.__version__, 'cuda_available', torch.cuda.is_available(), 'torch_cuda', torch.version.cuda)"
python -c "from torch.utils.cpp_extension import CUDA_HOME; print('CUDA_HOME', CUDA_HOME)"
nvcc -V
python -c "import importlib.util as u; print('DCNv3', u.find_spec('DCNv3')); print('mmdeploy', u.find_spec('mmdeploy'))"
```

`nvidia-smi`/GPU visibility answers only the driver/runtime part. `CUDA_HOME` and `nvcc` answer the source-build/toolkit part.

## Common failure modes

| Symptom | Likely cause | Safe triage | Resolution path |
| --- | --- | --- | --- |
| `NotImplementedError: Cuda is not availabel` while building DCNv3 | Upstream setup script found either `torch.cuda.is_available() == False` or `CUDA_HOME is None`. The typo is upstream. | Run the PyTorch CUDA and `CUDA_HOME` probes above. Check `nvcc -V`. | Install/select a CUDA-enabled PyTorch wheel and toolkit that match, or use a compatible prebuilt DCNv3 wheel. Do not retry source build in a CPU-only environment. |
| GPU visible in `nvidia-smi`, but DCNv3 build still fails | Driver/runtime exists, but CUDA toolkit or PyTorch CUDA wheel is absent/mismatched. | Compare `torch.version.cuda`, `CUDA_HOME`, and `nvcc -V`. | Use a coherent PyTorch+CUDA+toolkit environment. GPU visibility alone is insufficient. |
| `ModuleNotFoundError: No module named 'DCNv3'` | DCNv3 Python extension was not installed in the active environment, or the active environment differs from the build environment. | `python -c "import sys; print(sys.executable); import importlib.util as u; print(u.find_spec('DCNv3'))"` | Install a matching prebuilt wheel or build the workflow's `ops_dcnv3` package in the active environment after CUDA/toolkit checks. |
| `undefined symbol`, ABI, or import crash for `DCNv3` | Extension was compiled for a different PyTorch/CUDA/compiler ABI. | Print PyTorch version/CUDA and locate the imported `DCNv3` module without exposing private paths in reports. | Rebuild/reinstall DCNv3 inside the final runtime environment; avoid mixing wheels from another PyTorch/CUDA version. |
| `input must be a CUDA tensor` from DCNv3 kernel | Compiled CUDA op received CPU tensors or a CPU execution path tried to use the compiled module. | Confirm model/device placement and whether the code path uses `DCNv3` or `DCNv3_pytorch`. | Move model and inputs to CUDA for compiled-op execution, or switch to a documented pure PyTorch fallback only for debugging/guidance. |
| ONNX contains `mmdeploy::TRTDCNv3`, TensorRT parser fails | mmdeploy TensorRT backend lacks the InternImage custom plugin. | Confirm the mmdeploy build included `modulated_deform_conv_v3` and registered `TRTDCNv3`. | Rebuild mmdeploy TensorRT backend with the InternImage custom op before TensorRT conversion. |
| `ImportError` for `mmdeploy.backend.tensorrt` or `from_onnx` | mmdeploy not installed, wrong version, or installed without TensorRT backend support. | `python -c "import mmdeploy; print(mmdeploy.__version__); from mmdeploy.backend.tensorrt import from_onnx"` | Use the repo-compatible mmdeploy version/build and TensorRT backend dependencies. |
| CMake cannot find TensorRT or CUDNN | `TENSORRT_DIR`/`CUDNN_DIR` placeholders are unset or point to incompatible installs. | Echo the variables and inspect whether headers/libraries are present in those installation roots. | Set valid installation roots and rebuild. Stop if the user has not approved host-level dependency changes. |
| Detection/segmentation deploy import fails on `mmcv_custom`, `mmdet_custom`, or `mmseg_custom` | Command executed outside the expected task runtime context or plugin packages are not on `PYTHONPATH`. | Use the command builder's `cd <repo>/<task>` template; probe imports from that directory/environment. | Run deploy from the task subdirectory or set an explicit module search path for that checkout; keep OpenMMLab versions matched. |
| Detection/segmentation deploy starts on CPU by default but TensorRT is requested | The deploy parser default is `--device cpu`, while the documented TensorRT command uses `--device cuda`. | Inspect generated command template. | Pass `--device cuda` for TensorRT export after CUDA readiness is confirmed. |
| `Config file not found` or wrong model after export command | Model name, task family, dataset directory, or config path mismatch. | Generate a template with `build_export_command.py` and inspect the derived config path before running. | For detection use the dataset/config family that matches the model (for example COCO Mask R-CNN under `configs/coco`). For segmentation use the correct dataset family (for example ADE20K under `configs/ade20k`). |
| Checkpoint load key mismatch | Checkpoint does not match the model config/name or contains a different state dict layout. | Confirm the checkpoint naming and model config family; do not infer compatibility from file extension alone. | Obtain the matching checkpoint for that exact model/config or update the command to the right config. |
| Classification TensorRT check reports large output delta | Engine built with wrong input shape, wrong checkpoint/model, precision differences, or missing custom op behavior. | Compare model name suffix resolution, ONNX input shape, and TensorRT engine name generated from the model. | Re-export ONNX with the intended model and fixed shape; rebuild engine only after custom op and checkpoint compatibility are confirmed. |
| Export is slow, compiles unexpectedly, or consumes GPU memory | The user converted a dry-run template into a real build/export; mmdeploy/TensorRT and CUDA compilation are heavy. | Stop if the action was not approved. Inspect work dir and process list without deleting outputs blindly. | Resume only after user confirms resource budget, device, output directory, and whether partial build artifacts should be kept. |

## Triage workflow

1. Reproduce only the parser/template first:

   ```bash
   python sub-skills/deployment/scripts/build_export_command.py detection-trt --model-name <model-name>
   ```

2. Classify the requested action:
   - command construction only: no CUDA/OpenMMLab imports required;
   - ONNX export: PyTorch/model/checkpoint required, usually CUDA for InternImage export script;
   - TensorRT conversion: ONNX plus mmdeploy TensorRT backend and `TRTDCNv3` custom plugin;
   - DCNv3 source build: CUDA-enabled PyTorch plus `CUDA_HOME`/nvcc/toolkit.
3. Probe the active environment with the safe checks above.
4. Check the command template for task directory, config, checkpoint, image, work dir, and device.
5. Only then propose the next build/export command, and mark it as requiring user approval if it will compile, download, or use substantial GPU memory.

## Messages that should change the plan

- User says they only need a deployment plan: use the bundled command builder; do not install or build.
- User says they have GPU but no nvcc: recommend prebuilt DCNv3 or toolkit installation; do not run `make.sh` yet.
- User asks for TensorRT detection/segmentation export: verify mmdeploy custom op first; a plain mmdeploy install is not enough.
- User asks for CPU-only export: classification ONNX script calls `.cuda()`; detection/segmentation TensorRT is CUDA-oriented. Explain that CPU-only can still generate templates but does not verify exports.
- User provides a checkpoint but no config: infer only from the model-name convention when it is unambiguous; otherwise ask for the intended task/dataset config.
