# Install and Backend Notes

## Purpose

Read this when you need Open3D-ML importable and want to know which backend
choices are safe for the current machine.

## Verified private-inspection facts

- Open3D 0.19.0 imported successfully with PyTorch ops enabled.
- `open3d.ml.torch` imported successfully once PyTorch was downgraded to a
  compatible 2.2.* CPU wheel and NumPy was kept below 2.
- TensorFlow ops were not enabled in the verified Open3D wheel.
- CUDA hardware was visible on the host, but a CPU smoke path was sufficient
  for import verification.

## Public install patterns

### CPU PyTorch path

A conservative install for import and API inspection is:

```bash
python -m pip install open3d 'torch==2.2.*+cpu' 'torchvision==0.17.*+cpu' \
  addict numpy<2 pyyaml tensorboard
```

If your platform or wheel index uses a different compatible PyTorch release,
choose a pair that satisfies both the Open3D wheel and the Open3D-ML import
check. The key requirement is that `open3d.ml.torch` imports cleanly.

### CUDA PyTorch path

If you need GPU execution, install a CUDA-matched `torch`/`torchvision` wheel
pair and make sure the Open3D build you use was compiled with the matching
backend assumptions. Treat the GPU path as a separate compatibility check from
CPU importability.

### TensorFlow path

TensorFlow support depends on how Open3D was built. On Linux, the PyPI Open3D
wheel may not expose TensorFlow ops. If TensorFlow is required, prefer an
Open3D build that explicitly includes TensorFlow support.

### OpenVINO path

OpenVINO is optional and version-sensitive. Install it only when you need the
wrapper and you know the supported model/backend combination is available.

## Source-checkout integration

If you are using an Open3D wheel plus a local Open3D-ML checkout, set
`OPEN3D_ML_ROOT` to the checkout root before importing `open3d.ml.*`.
That tells Open3D where to find the `ml3d` source tree.

Example:

```bash
export OPEN3D_ML_ROOT=/path/to/Open3D-ML
python -c "import open3d.ml.torch as ml3d; print(ml3d.__name__)"
```

Do not point future agents at a specific machine path. Use the environment
variable generically.

## Safe smoke checks

Run these after install:

```bash
python -m pip check
python -c "import open3d as o3d; print(o3d.__version__)"
python -c "import open3d.ml.torch as ml3d; print(ml3d.models.RandLANet.__name__)"
```

If you are using a source checkout, add `OPEN3D_ML_ROOT` to the environment
for the import command above.

## When to stop and reassess

Stop and reassess the environment if:

- `open3d.ml.torch` raises a version-mismatch error.
- NumPy and compiled extensions disagree on ABI compatibility.
- The wheel lacks TensorFlow ops and TensorFlow is a required backend.
- The machine does not expose the GPU/backend required for the requested
  verification target.
