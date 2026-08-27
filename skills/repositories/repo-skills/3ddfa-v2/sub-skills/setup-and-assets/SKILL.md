---
name: "setup-and-assets"
description: "Prepare 3DDFA_V2 runtime assets and native extension builds before
  demos or benchmarks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Setup and assets

Use this sub-skill before any 3DDFA_V2 demo or benchmark, and whenever a user
reports missing checkpoints, failed imports, or native-build errors.

## When to read

Read this sub-skill when the task mentions:

- `build.sh`, `build_cpu_nms.sh`, `build_sim3dr.sh`, `render.so`, `cpu_nms`, or
  `Sim3DR_Cython`.
- Missing checkpoints, BFM files, config YAML files, or ONNX artifacts.
- Import errors from `FaceBoxes`, `TDDFA`, `utils.render`, `Sim3DR`, or
  `onnxruntime`.
- NumPy alias errors such as `np.long` or Cython errors such as `np.int_t`.

## Preparation workflow

1. **Check assets.** Run the bundled asset checker against the checkout root.
   It reads the selected YAML config and reports missing checkpoints, BFM files,
   and sample inputs.
2. **Build native extensions.** Build FaceBoxes NMS, Sim3DR, and `render.so` in
   that order. These are needed even for many headless demo paths because the
   top-level scripts import rendering modules.
3. **Smoke-test imports.** Run the core import helper; it loads `FaceBoxes`,
   constructs `TDDFA` from the default config, imports the ONNX classes, and
   verifies the render import surface.
4. **Only then route onward.** Send still-image requests to
   `../still-image-demo/`, video/tracking requests to `../video-and-tracking/`,
   and ONNX/benchmark requests to `../onnx-and-benchmarking/`.

## Bundled helpers

Use these root-level helper scripts from this generated skill:

- `../../scripts/check_assets.py` — validates required model/config/sample files.
- `../../scripts/build_native_extensions.py` — reproduces the native build steps
  with explicit commands.
- `../../scripts/check_core_imports.py` — import and constructor smoke test.
- `../../scripts/bootstrap_runtime.py` — shared NumPy/headless/runtime bootstrap
  used by the wrapper scripts.

Example pattern:

```bash
python <skill-root>/scripts/check_assets.py --repo-root <checkout>
python <skill-root>/scripts/build_native_extensions.py --repo-root <checkout>
python <skill-root>/scripts/check_core_imports.py --repo-root <checkout>
```

Do not copy private environment paths into user-facing notes. Describe the
required packages generically: Python 3.10/3.11, torch/torchvision, OpenCV,
imageio/imageio-ffmpeg, PyYAML, tqdm, Cython, SciPy, matplotlib, and
onnxruntime.

## Dependency and backend decisions

- CPU is sufficient for the selected core workflows.
- CUDA is an optional speed path through `-m gpu`; it is not required for the
  generated skill's baseline verification.
- Use Cython 0.29.x if FaceBoxes NMS fails under Cython 3.x.
- Use a NumPy compatibility shim or a conservative NumPy pin if `np.long` or
  similar aliases fail at import time.
- The helper scripts set headless plotting defaults so still-image commands do
  not block on GUI display in non-interactive environments.

## Asset responsibilities

Read `references/build-and-assets.md` for the build order and asset checklist.
Read `../../references/model-assets.md` for checkpoint/config purposes and
public download notes. Read `references/troubleshooting.md` for setup-specific
failure recovery.

## Boundaries

This sub-skill owns setup, assets, and import smoke checks. It does not own
choosing demo output modes, video smoothing windows, or interpreting latency
numbers except where those tasks fail because setup is incomplete.
