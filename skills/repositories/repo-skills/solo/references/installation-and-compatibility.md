# Installation and compatibility

SOLO is an older MMDetection implementation. Its `setup.py` builds Cython and
CUDA extensions rather than behaving like a pure-Python package.

## Minimum documented stack

- Linux is the supported platform.
- Python 3.5+ is documented; Python 3.7/3.8 is a safer target for this
  revision and for old PyTorch wheels.
- PyTorch 1.1+ is documented, but the project says versions >=1.5 were not
  tested. Match the torch/torchvision pair and the CUDA runtime used to build
  extensions.
- `mmcv==0.2.16` is required by the repository's runtime requirements.
- Build requirements include Cython and NumPy. Runtime requirements include
  NumPy, SciPy, Pillow, matplotlib, six, terminaltables, torch, torchvision,
  and mmcv. `albumentations` and `imagecorruptions` are optional.
- COCO evaluation requires a compatible `pycocotools` installation; do not
  assume the newest release works with an old NumPy/torch stack.

Use a fresh private environment for legacy dependency experiments. Do not
upgrade a working project environment merely to satisfy this guide.

## Extension build gate

The repository declares CUDA extensions for NMS, ROI align/pool, deformable
convolution/pooling, sigmoid focal loss, masked convolution, and a compiling
info helper, plus a Cython Soft-NMS module. A successful `pip install` is not
proof that these modules work. Before building, verify:

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.version.cuda)
print(torch.cuda.is_available())
PY
nvcc --version
```

Set `CUDA_HOME` to the toolkit used by the installed torch build, use a
compatible compiler, and rebuild after changing torch, CUDA, or the source
revision. A host may expose an NVIDIA driver and a torch CUDA runtime while
still lacking `nvcc`; that is a build block, not a CPU fallback.

Symptoms such as `CUDA_HOME environment variable is not set`, `nvcc not
found`, missing `*_cuda` modules, undefined symbols, or ABI errors mean the
extension gate is not satisfied. Stop before model execution, record the exact
versions, and repair the environment or narrow the claim.

## Installation shape

For a normal supported checkout, install build requirements, install the
package editable, and then run the package/import diagnostics. Keep dataset
roots, checkpoints, and output directories outside the package. The generated
skill intentionally does not reproduce a checkout-specific command: future
agents must use the public repository/package source they have selected and
must not assume this generated skill contains configs or weights.

## Verification ladder

1. `python -m pip check` and import `torch`, `mmcv`, and `mmdet`.
2. Confirm `mmcv.__version__` is `0.2.16` and inspect torch/CUDA versions.
3. Import the public API and model/data registries.
4. Import each required custom operator and run a tiny tensor operation.
5. Construct a representative config with pretrained weights disabled.
6. Only then attempt local inference or dataset-scale training/evaluation.

If step 3 or 4 fails, keep the failure visible. Do not make a generated skill
claim that a CPU-only import validates the GPU workflow.
