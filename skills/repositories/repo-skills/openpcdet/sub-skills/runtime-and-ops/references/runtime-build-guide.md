# Runtime Build Guide

## Minimum stack for full workflows

OpenPCDet is GPU-first. A usable full-workflow environment needs:

- Python with `pcdet` installed from the checkout.
- PyTorch built for the CUDA runtime you intend to use.
- CUDA toolkit headers and `nvcc` for compiling OpenPCDet native extensions.
- A matching `spconv`/`cumm` wheel variant.
- OpenPCDet native extensions compiled from `setup.py`.
- Dataset-specific optional packages only for selected datasets.
- Visualization packages only when using interactive demo drawing.

The construction environment verified `pcdet==0.6.0+233f849`, PyTorch CUDA 12.4, `spconv-cu124`, CUDA GPUs, and all OpenPCDet compiled extension imports. Do not expose private environment paths in user-facing guidance.

## Editable build checklist

Before building:

1. Verify `python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"`.
2. Choose the matching spconv wheel suffix, such as `spconv-cu124` for CUDA 12.4 PyTorch.
3. Confirm `nvcc --version` and CUDA headers are visible.
4. Set `TORCH_CUDA_ARCH_LIST` to the target GPU architectures when the environment does not infer them correctly.
5. Limit `MAX_JOBS` if compiling on memory-constrained hosts.

Build command shape:

```bash
python -m pip install --no-build-isolation -e <OpenPCDet-checkout>
```

## Construction-time pitfalls and fixes

These are not permanent public environment paths; they are patterns to recognize:

- Missing `cicc`, `ptxas`, `libnvvm`, or `libdevice`: the CUDA toolkit installation is incomplete or `CUDA_HOME` does not point at the toolkit root.
- Linker cannot find `-lcudart`: the CUDA runtime package may provide only a versioned `libcudart.so.*`; create an environment-local unversioned symlink or use a toolkit distribution that provides it.
- `cuda_fp16.h` cannot find `nv/target`: CUDA 12 headers need CCCL headers. Make `nv`, `thrust`, `cub`, and `cuda` header subtrees visible under the active CUDA include root or install a complete CUDA toolkit.
- Adding an incompatible CCCL include root can shadow C/C++ standard library headers; prefer a consistent full toolkit or expose CCCL subtrees in the toolkit include layout.
- `pcdet.datasets` import fails inside Argo2/kornia TorchScript: use a kornia version compatible with the active PyTorch; `kornia==0.6.12` was verified with the construction stack.

## Optional dependencies

- Open3D or Mayavi is needed for interactive demo visualization; either can be omitted for non-visual inference adaptations.
- `av2`, kornia, and related geometry dependencies are relevant for Argoverse2 workflows.
- Dataset devkits for NuScenes, Lyft, Waymo, and Pandaset must match the selected dataset conversion workflow.

## Do not overclaim

A successful import of `pcdet` alone does not prove:

- compiled ops are importable,
- spconv kernels work on the active GPU,
- dataset info/database files exist,
- configs match checkpoints,
- full training/evaluation can run within memory/time budgets.

Use the root runtime inspector plus dataset/config checks before expensive work.
