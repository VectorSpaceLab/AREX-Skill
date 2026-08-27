# Environment and CUDA extension setup

## Baseline and compatibility

The repository README documents its original validation environment as
Python 3.7.3, PyTorch 1.9.0, and CUDA 11.1, and notes that other versions may
work. `requirements.txt` adds Cython, torchvision, SciPy, termcolor, addict,
yapf, timm, Submitit, `pycocotools`, and `panopticapi`. Treat the README
versions as historical guidance, not a guarantee for a modern installation.
Keep PyTorch and torchvision from a compatible release family, and make the
CUDA toolkit/compiler used to build the extension compatible with the CUDA
runtime expected by PyTorch.

The verified inspection run for this repository used a generic CUDA 12.1
stack with torch 2.5.1+cu121, CUDA 12.1 `nvcc`, GCC 12.4, and an A100 with
compute capability 8.0. The extension compiled and imported, COCO dependencies
imported, and `pip check` passed. These are evidence for that tested
combination, not a promise that every GPU, driver, compiler, or PyTorch build
will work.

## Read-only package/backend probe

From an activated environment, run the bundled checker from the repository
root:

```bash
python skills/disco/dino/sub-skills/data-model-setup/scripts/check_dino_environment.py --help
python skills/disco/dino/sub-skills/data-model-setup/scripts/check_dino_environment.py \
  --require-extension --require-coco --pip-check
```

Add `--require-cuda` for a CUDA-required DINO run. Use `--json` for a
machine-readable report. The checker does not install packages, build an
extension, reserve a device, or alter environment variables. `--smoke-cuda`
allocates a small tensor and `--smoke-extension` calls a tiny custom-op forward;
both should be used only when a free GPU is expected. CUDA context creation
can fail when all visible devices are occupied. A checker warning that
`CUDA_HOME`/`nvcc` is not visible is actionable for a future source build even
when an already-installed extension imports successfully; distinguish it from
the extension-runtime gate.

Typical required imports are:

```text
torch, torchvision, pycocotools, panopticapi (only for panoptic),
MultiScaleDeformableAttention (for standard DINO deformable attention)
```

## Install dependencies

Use a clean virtual environment or an approved project environment, then
install a PyTorch/torchvision pair from the same compatibility table and
install the repository requirements:

```bash
python -m pip install -r requirements.txt
python -m pip check
```

If the repository-pinned Git source for `pycocotools` fails because generated
C sources are absent or the build toolchain is unsuitable, use a compatible
published `pycocotools` wheel only when its version/API is acceptable for the
run. Record that substitution. `panopticapi` is optional for bounding-box
DINO but required by the panoptic loader.

## Build the MultiScaleDeformableAttention extension

The repository's documented build is:

```bash
cd models/dino/ops
python setup.py build install
python test.py
cd ../../..
```

Before running it, verify all of the following:

- `python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"`
  reports the intended CUDA-enabled PyTorch and a visible device;
- `python -c "from torch.utils.cpp_extension import CUDA_HOME; print(CUDA_HOME)"`
  reports a usable toolkit root, or set `CUDA_HOME` explicitly;
- `nvcc --version` and the PyTorch CUDA family are compatible;
- `nvcc` can find CUDA runtime/development headers and the C++ compiler can
  find PyTorch headers;
- the host compiler is supported by the toolkit. If the toolchain rejects a
  newer compiler, select a compatible GCC/G++ (on the verified host, GCC <=12
  was required); do not force an unsupported compiler silently;
- CUDA 12 builds can require explicit CCCL/Thrust include directories. If
  errors mention `cuda/std`, `cuda/cccl`, or missing CCCL headers, add the
  toolkit's appropriate `targets/<arch>/include/cccl` directory to `CPATH`
  or the extension's include configuration. Use paths from the active
  environment, never copied private paths;
- choose `TORCH_CUDA_ARCH_LIST` for the target GPU when auto-detection is not
  reliable (for example `8.0` for an A100), and ensure the resulting binary is
  usable by the target compute capability;
- compile while a GPU is free. The setup script only chooses the CUDA branch
  when `torch.cuda.is_available()` and `CUDA_HOME` are present, and the test
  allocates CUDA tensors.

A generic explicit build pattern is:

```bash
export CUDA_HOME=/path/to/compatible/cuda
export CC=/path/to/supported/gcc
export CXX=/path/to/supported/g++
export TORCH_CUDA_ARCH_LIST="8.0"       # replace with the target capability
# If required by CUDA 12.x, use the active toolkit's CCCL include directory:
export CPATH="$CUDA_HOME/targets/x86_64-linux/include/cccl:${CPATH:-}"
python models/dino/ops/setup.py build install
python models/dino/ops/test.py
```

`CUDA_HOME`, compiler, architecture, and include paths above are placeholders.
Do not hard-code a machine-specific prefix into a skill or report. Build
commands may need a cleaned `build/` directory or a reinstall after changing
PyTorch, CUDA, compiler, or architecture; cleanup is an operator decision,
not performed by the bundled scripts.

## Verification levels

- **Static:** imports and source/config inspection only; no claim of backend
  execution.
- **CUDA smoke:** import the extension and allocate a tiny CUDA tensor.
- **Operator test:** run `models/dino/ops/test.py`; it compares CUDA forward
  output with the PyTorch reference and runs numerical gradient checks for
  several channel widths. This needs a free CUDA device and can be expensive.
- **Model build smoke:** parse a selected config and construct the model in a
  suitable environment. This may instantiate pretrained-backbone code and
  should not be confused with a training result.

The verified repository environment passed package imports, CUDA allocation,
extension import, config parsing, and extension compilation. It did not
validate long training, full evaluation, Slurm/Submitit service behavior,
pretrained Swin/ConvNeXt downloads, or a full COCO dataset because those
artifacts were intentionally not acquired.
