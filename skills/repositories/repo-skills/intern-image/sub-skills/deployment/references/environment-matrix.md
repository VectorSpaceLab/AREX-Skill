# Deployment environment matrix

This matrix distills installation/export facts for InternImage deployment planning. It is intentionally prerequisite-focused: printing command templates is safe in a CPU environment, but running exports or builds is not.

## Verification baseline from construction

- Skill drafting environment: CPU-safe inspection and generated helper checks only.
- Full CUDA/TensorRT stack was not installed or verified during construction.
- Host evidence showed NVIDIA GPUs and a modern driver, but `nvcc` was absent. This proves the key distinction: GPU visibility and a CUDA runtime do not imply source-build readiness.
- No OpenMMLab, PyTorch CUDA, DCNv3 source build, mmdeploy, TensorRT, or SAM runtime verification was claimed for this sub-skill.

## Compatibility layers

| Layer | Needed for | Evidence-backed pins or requirements | Safe check | Blocking if missing |
| --- | --- | --- | --- | --- |
| Python | all workflows | Python 3.9 was used in repo installation instructions and inspection. | `python --version` | Use an environment compatible with the selected OpenMMLab/PyTorch pins. |
| CUDA driver/runtime | PyTorch CUDA tensors, model inference, exports | CUDA >= 10.2 with CUDNN >= 7 was documented. Example wheel: `torch==1.11.0+cu113`, `torchvision==0.12.0+cu113`. | `nvidia-smi`; `python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"` | TensorRT export and DCNv3 tests cannot be considered verified. |
| CUDA toolkit/nvcc | DCNv3 source build, mmdeploy TensorRT backend op build | `nvcc -V` must match or be compatible with the PyTorch CUDA/toolchain target. | `nvcc -V`; `python -c "from torch.utils.cpp_extension import CUDA_HOME; print(CUDA_HOME)"` | Source build raises `Cuda is not availabel` or CMake/mmdeploy build fails. |
| DCNv3 Python extension | InternImage compiled operator runtime | Package name `DCNv3`, version `1.1` in the repo setup scripts. Prebuilt wheels were documented as an alternative. | `python -c "import DCNv3; print(DCNv3)"` | Model forward/export using compiled operator fails; native `ops_dcnv3/test.py` cannot run. |
| Classification Python deps | classification ONNX/TensorRT export | `timm==0.6.11`, `mmcv-full==1.5.0`, `mmsegmentation==0.27.0`, `mmdet==2.28.1`, plus `opencv-python`, `termcolor`, `yacs`, `pyyaml`, `scipy`, `numpy<2` (example `1.26.4`), `pydantic==1.10.13`. | import torch/timm/mmcv/yacs and load the selected YAML config before export. | `classification/export.py` cannot build/load the model. |
| Detection Python deps | detection TensorRT export | Detection install matched MMDetection v2.28.1 era: `mmcv-full==1.5.0`, `mmsegmentation==0.27.0`, `mmdet==2.28.1`, `timm==0.6.11`, `numpy<2`, `pydantic==1.10.13`, `yapf==0.40.1`. | import `mmcv_custom`, `mmdet_custom`, `mmdet`, `mmdeploy` from the detection runtime context. | `detection/deploy.py` import or config/plugin registration fails. |
| Segmentation Python deps | segmentation TensorRT export | Segmentation install matched MMSegmentation v0.27.0 era with `mmcv-full==1.5.0`, `mmsegmentation==0.27.0`, `mmdet==2.28.1`, `timm==0.6.11`, `numpy<2`, `pydantic==1.10.13`. | import `mmcv_custom`, `mmseg_custom`, `mmseg`, `mmdeploy` from the segmentation runtime context. | `segmentation/deploy.py` import or custom backbone registration fails. |
| mmdeploy Python package | ONNX to backend conversion; deploy scripts | Repo export sections install `mmdeploy==0.14.0`; TensorRT build sequence checks out mmdeploy `v0.13.0` before custom-op compilation. Treat this as a tight compatibility surface and avoid mixing arbitrary versions. | `python -c "import mmdeploy; print(mmdeploy.__version__)"` plus backend-specific imports. | Export scripts may import but fail at TensorRT backend conversion or unsupported custom op. |
| TensorRT + CUDNN | engine conversion and runtime | The custom-op CMake template requires `TENSORRT_DIR` and `CUDNN_DIR`; deployment target backend is `trt`. | inspect environment variables and verify TensorRT Python/C++ libraries are installed. | TensorRT engine build cannot run. |
| mmdeploy TensorRT `TRTDCNv3` op | DCNv3-backed TensorRT engine | Build/copy `modulated_deform_conv_v3` into mmdeploy backend ops before `make install`. | Confirm the mmdeploy build included the custom source and exports/registers `TRTDCNv3`. | ONNX may contain `mmdeploy::TRTDCNv3` but TensorRT parsing/build fails. |

## Export-mode prerequisites

| Mode | Minimum command-template prerequisites | Runtime prerequisites before execution | Native verification expectation |
| --- | --- | --- | --- |
| `classification-onnx` | model name, checkpoint directory, chosen repo checkout path placeholder | PyTorch CUDA environment, classification dependencies, checkpoint, selected YAML config, compiled DCNv3 if the model path uses compiled op | optional export run only after GPU/checkpoint approval; builder `--help` is safe. |
| `classification-trt` | all ONNX fields plus mmdeploy/TensorRT placeholders | classification ONNX succeeds; mmdeploy TensorRT backend installed; TensorRT/CUDNN available; `TRTDCNv3` custom op built | optional TensorRT run only after backend approval. |
| `detection-trt` | deploy config, model config, checkpoint, sample image, work dir | MMDetection 2.x stack, `mmcv_custom` and `mmdet_custom` registration, CUDA device, mmdeploy/TensorRT with `TRTDCNv3` | optional conversion skipped unless GPU/TensorRT/checkpoint approved. |
| `segmentation-trt` | deploy config, model config, checkpoint, sample image, work dir | MMSegmentation 0.x stack, `mmcv_custom` and `mmseg_custom` registration, CUDA device, mmdeploy/TensorRT with `TRTDCNv3` | optional conversion skipped unless GPU/TensorRT/checkpoint approved. |

## Version and dependency cautions

- OpenMMLab 1.x-era packages are sensitive to PyTorch, CUDA, compiler, and Python versions. Use the documented pins as the starting point rather than latest releases.
- Keep NumPy below 2.0 for this repo's documented stacks.
- Detection explicitly pinned `yapf==0.40.1` to avoid config formatting compatibility issues.
- The repository notes that conda OpenCV can break torchvision GPU support; prefer `opencv-python` from pip when following the documented environment shape.
- Do not use a CPU-only inspection environment as evidence for TensorRT, DCNv3 CUDA, or mmdeploy backend readiness.

## Stop conditions

Stop and ask for environment repair or scope narrowing when:

- the user asks for a real export but no checkpoint path or model/config pairing is known;
- `torch.cuda.is_available()` is false for a TensorRT/DCNv3 execution request;
- `CUDA_HOME` or `nvcc` is missing for a source build request;
- mmdeploy imports but TensorRT backend support or the `TRTDCNv3` custom op was not built;
- OpenMMLab versions are latest/unknown and not matched to the repo's documented 2.x/0.x stack;
- a command would download large checkpoints, compile C++/CUDA, or run dataset-scale inference without explicit approval.
