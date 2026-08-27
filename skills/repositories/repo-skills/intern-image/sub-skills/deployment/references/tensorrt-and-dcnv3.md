# TensorRT and DCNv3 deployment reference

This reference distills InternImage deployment evidence for later operation without reopening the original documentation. Evidence labels include `README.md`, task READMEs, `classification/export.py`, `detection/deploy.py`, `segmentation/deploy.py`, the three `ops_dcnv3/` trees, and `tensorrt/modulated_deform_conv_v3/*`.

## DCNv3 surfaces

InternImage uses DCNv3 as a core operator. There are separate but structurally similar operator trees for classification, detection, and segmentation. Each tree contains:

- `setup.py`: builds the Python package named `DCNv3`, version `1.1`, using `torch.utils.cpp_extension.CUDAExtension` only when `torch.cuda.is_available()` is true and `CUDA_HOME` is not `None`.
- `make.sh`: runs `python setup.py build install`.
- `functions/dcnv3_func.py`: defines `DCNv3Function`; ONNX export emits the custom symbolic op `mmdeploy::TRTDCNv3`.
- `modules/dcnv3.py`: provides both `DCNv3_pytorch` and compiled `DCNv3` modules. The pure PyTorch path is for debugging/fallback reasoning and is not a proof that production CUDA training/export works.
- `test.py`: compares CUDA output/gradients against the PyTorch implementation and times forward passes. It requires a built `DCNv3` extension and CUDA tensors.

The operator build deliberately stops with the misspelled upstream error text `Cuda is not availabel` when either PyTorch cannot see CUDA or the CUDA toolkit path (`CUDA_HOME`, normally from nvcc/toolkit installation) is missing. A machine can have visible GPUs and still fail this source build if only the CUDA runtime/driver is available.

## When to build DCNv3

Build or install DCNv3 only when a later action needs compiled CUDA kernels: full model training/evaluation/demo, TensorRT export validation, or native DCNv3 numerical tests. Do not build merely to print command templates or inspect configs.

Preferred decision sequence:

1. Confirm the target workflow: classification, detection, segmentation, or autonomous-driving baseline.
2. Confirm a CUDA-enabled PyTorch wheel matching the host driver/toolkit target.
3. Check toolkit availability separately: `nvcc -V` and a Python check for `torch.utils.cpp_extension.CUDA_HOME`.
4. If a matching prebuilt `DCNv3` wheel exists for the target PyTorch/CUDA combination, prefer it over a source build.
5. If compiling from source, build the operator tree for the workflow that will execute. Reusing a separately built `DCNv3` package can work only if version, ABI, PyTorch, CUDA, and code variant match.
6. Run the operator `test.py` only after build approval; it exercises CUDA tensors and includes timing loops.

## TensorRT custom operator requirement

TensorRT export through mmdeploy is not complete with the Python `DCNv3` package alone. The ONNX symbolic op is `mmdeploy::TRTDCNv3`, and TensorRT needs an mmdeploy backend plugin compiled from the bundled C++/CUDA sources:

- `tensorrt/modulated_deform_conv_v3/trt_deform_conv_v3.cpp`
- `tensorrt/modulated_deform_conv_v3/trt_deform_conv_v3.hpp`
- `tensorrt/modulated_deform_conv_v3/trt_deform_conv_v3_kernel.cu`
- `tensorrt/modulated_deform_conv_v3/trt_deform_conv_v3_kernel.hpp`

These sources register a TensorRT plugin named `TRTDCNv3`. They were not copied into this skill because they are C++/CUDA build inputs tied to an mmdeploy source tree and TensorRT/CUDNN installation. The safe bundled replacement is `scripts/build_export_command.py`, which prints prerequisite-aware command templates and makes the custom-op copy/build step explicit.

## mmdeploy/TensorRT build template

Use this as a command template, not as an automatic action. Replace placeholders with user-provided paths and stop if any prerequisite is missing.

```bash
export INTERNIMAGE_REPO=<INTERNIMAGE_REPO>
export MMDEPLOY_DIR=<MMDEPLOY_DIR>
export TENSORRT_DIR=<TENSORRT_DIR>
export CUDNN_DIR=<CUDNN_DIR>

# Build mmdeploy with the InternImage TensorRT backend op.
mkdir -p "${MMDEPLOY_DIR}/csrc/mmdeploy/backend_ops/tensorrt"
cp -r "${INTERNIMAGE_REPO}/tensorrt/modulated_deform_conv_v3" \
  "${MMDEPLOY_DIR}/csrc/mmdeploy/backend_ops/tensorrt/"
cd "${MMDEPLOY_DIR}"
mkdir -p build
cd build
cmake -DCMAKE_CXX_COMPILER=g++ \
  -DMMDEPLOY_TARGET_BACKENDS=trt \
  -DTENSORRT_DIR="${TENSORRT_DIR}" \
  -DCUDNN_DIR="${CUDNN_DIR}" \
  ..
make -j"$(nproc)"
make install
cd "${MMDEPLOY_DIR}"
python -m pip install -e .
```

The root TensorRT section used `g++-7`; the classification export section used `g++`. Choose a compiler that matches the local CUDA/TensorRT/mmdeploy support matrix rather than assuming either name exists.

## Export command semantics

Use the bundled command builder to emit these templates with placeholders or concrete paths:

```bash
python sub-skills/deployment/scripts/build_export_command.py classification-onnx \
  --model-name internimage_t_1k_224 --ckpt-dir <checkpoint-dir>

python sub-skills/deployment/scripts/build_export_command.py classification-trt \
  --model-name internimage_t_1k_224 --ckpt-dir <checkpoint-dir> --include-mmdeploy-build

python sub-skills/deployment/scripts/build_export_command.py detection-trt \
  --model-name mask_rcnn_internimage_t_fpn_1x_coco --checkpoint <checkpoint.pth>

python sub-skills/deployment/scripts/build_export_command.py segmentation-trt \
  --model-name upernet_internimage_t_512_160k_ade20k --checkpoint <checkpoint.pth>
```

The generated templates are dry-run plans. They do not download checkpoints, install packages, build operators, or execute export. Before turning a template into an action, confirm:

- checkpoint path exists and matches the config/model name;
- input resolution matches the classification model suffix or mmdeploy deploy config;
- `DCNv3` Python package imports in the target environment when the model uses the compiled operator;
- mmdeploy imports and includes TensorRT backend support;
- TensorRT custom plugin for `TRTDCNv3` has been built into mmdeploy;
- export device is CUDA for TensorRT workflows;
- work directory is writable and not shared with an unrelated model.

## Source-script decisions

| Evidence label | Decision | Bundled handling | Reason |
| --- | --- | --- | --- |
| `classification/export.py` | Adapt | `scripts/build_export_command.py` prints ONNX and TensorRT templates for `--model_name`, `--ckpt_dir`, `--onnx`, and `--trt`. | Actual export imports torch/model code, loads checkpoints, uses CUDA, and may call TensorRT. |
| `detection/deploy.py` | Adapt | The builder prints mmdeploy positional args plus `--work-dir`, `--device cuda`, and optional `--dump-info`/quant flags. | Real conversion requires MMDetection, mmcv custom imports, checkpoint, sample image, mmdeploy, TensorRT, and custom op. |
| `segmentation/deploy.py` | Adapt | The builder prints the analogous MMSegmentation TensorRT command. | Real conversion requires MMSegmentation, mmcv/mmseg custom imports, checkpoint, sample image, mmdeploy, TensorRT, and custom op. |
| `ops_dcnv3/make.sh` and `setup.py` | Reference-only | Build prerequisites and failure triage are distilled here and in troubleshooting. | Source builds are backend-mutating and require explicit approval. |
| `tensorrt/modulated_deform_conv_v3/*` | Reference-only | The mmdeploy build template copies these C++/CUDA files from a user's checkout when export is approved. | They are not standalone Python helpers and must be compiled inside a matching mmdeploy tree. |
