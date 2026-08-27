# Troubleshooting

## `open3d.ml.torch` import fails

**Symptoms**
- `ModuleNotFoundError: No module named 'open3d.ml'`
- `ImportError` or version-mismatch messages from `open3d.ml.torch`

**Likely causes**
- `OPEN3D_ML_ROOT` is unset while using a source checkout with an external
  Open3D wheel.
- The installed torch wheel does not satisfy the Open3D wheel's expected
  version band.
- The Open3D wheel and backend stack were built for different ABI or backend
  combinations.

**Recovery**
1. Set `OPEN3D_ML_ROOT` to the checkout root if you are using source locally.
2. Reinstall a torch/torchvision pair that matches the Open3D wheel's expected
   version.
3. Re-run `scripts/check_open3d_ml.py --framework torch`.

## NumPy / compiled-extension mismatch

**Symptoms**
- Warnings about modules compiled against NumPy 1.x not running under NumPy 2.x
- Torch or Open3D extension imports that fail after a NumPy upgrade

**Likely causes**
- The selected wheel stack was built for a different NumPy ABI.

**Recovery**
1. Keep NumPy inside the version band recommended by the wheel stack.
2. Reinstall the private prefix instead of mutating a shared environment.
3. Re-run `python -m pip check` and the smoke helper.

## TensorFlow unavailable

**Symptoms**
- `open3d.ml.tf` import fails.
- Open3D build reports that TensorFlow ops are not enabled.

**Likely causes**
- The installed Open3D wheel was not built with TensorFlow support.
- You are on a platform where the wheel packaging does not expose TF ops.

**Recovery**
- Treat TensorFlow as optional unless your task explicitly requires it.
- If TF is required, prepare a TensorFlow-capable Open3D build before
  continuing.

## CUDA or GPU checks fail

**Symptoms**
- `torch.cuda.is_available()` is false.
- A GPU-only task requests CUDA but the smoke helper only sees CPU.

**Likely causes**
- The machine does not have a working CUDA driver/runtime pairing.
- The installed torch wheel is CPU-only.

**Recovery**
- Use the CPU path for import and API inspection.
- Prepare a CUDA-specific environment only when the task truly needs GPU
  runtime evidence.

## OpenVINO unsupported

**Symptoms**
- `open3d.ml` import works, but the OpenVINO wrapper is unavailable or the
  target model is not supported.

**Likely causes**
- The OpenVINO package is missing or the model/backend combination is outside
  the supported set.

**Recovery**
- Restrict OpenVINO use to the supported model list.
- Treat OpenVINO as optional unless the task specifically targets that wrapper.

## GUI/headless issues

**Symptoms**
- Visualizer startup errors or a missing GUI build.

**Likely causes**
- The Open3D wheel lacks GUI support or the current machine is headless.

**Recovery**
- Use fixture-based data checks or tensorboard summary generation instead of
  launching the GUI.
- Route visualization tasks to the visualization sub-skill, which explains the
  headless fallback.
