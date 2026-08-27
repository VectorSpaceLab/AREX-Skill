# Build and asset guide

## Build order

Build the native pieces in this order:

1. FaceBoxes CPU NMS extension.
2. Sim3DR Cython extension.
3. `utils/asset/render.so`.
4. Core import smoke after the build.

The root helper `../../scripts/build_native_extensions.py` reproduces that order
with explicit commands and verifies the resulting artifacts.

## Asset checklist

Before running any demo or benchmark, verify these files exist in the checkout:

- `FaceBoxes/weights/FaceBoxesProd.pth`
- `configs/bfm_noneck_v3.pkl`
- `configs/tri.pkl`
- `configs/BFM_UV.mat`
- `configs/indices.npy`
- `configs/param_mean_std_62d_120x120.pkl`
- `weights/mb1_120x120.pth`
- `weights/mb05_120x120.pth`

Use `../../scripts/check_assets.py` to check that list against the checkout's
chosen config file.

## What each asset does

- The FaceBoxes checkpoint powers the detector stage.
- The `bfm_noneck_v3.pkl` / `tri.pkl` pair powers 3D reconstruction and render
  outputs.
- `BFM_UV.mat` and `indices.npy` power UV texture output.
- `param_mean_std_62d_120x120.pkl` matches the default 62D MobileNet config.
- `mb1_120x120.pth` is the default checkpoint for `configs/mb1_120x120.yml`.
- `mb05_120x120.pth` is the smaller, faster MobileNet checkpoint.

## ONNX assets

The ONNX workflows can auto-generate these files if they are absent:

- `weights/mb1_120x120.onnx`
- `FaceBoxes/weights/FaceBoxesProd.onnx`
- `configs/bfm_noneck_v3.onnx`

Those files are optional for setup, but they matter for the benchmark sub-skill.

## Import smoke

After the build, run `../../scripts/check_core_imports.py` to confirm that
`FaceBoxes`, `TDDFA`, `TDDFA_ONNX`, and `utils.render` import from the checkout
with the prepared environment.
