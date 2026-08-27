# Cross-cutting Troubleshooting

## Start with the Diagnostic

From this skill root, run:

```bash
python scripts/check_3ddfa_environment.py --repo-root /path/to/3DDFA
```

If the failure is workflow-specific, continue with the nearest sub-skill troubleshooting reference.

## Common Failure Surfaces

| Symptom | Likely cause | Next step |
|---|---|---|
| `ModuleNotFoundError: dlib` before any CLI help appears | Native image/video scripts import `dlib` at top level. | Use `python-inference` troubleshooting; install dlib or patch/wrap the CLI for bbox-only operation. |
| `cannot import name 'mesh_core_cython' from 'utils.cython'` | Cython render extension has not been built for the active Python. | Build `utils/cython` in the target checkout or avoid render-dependent native startup paths. |
| `FileNotFoundError` for `train.configs/*` | 3DMM/whitening/PAF/PNCC arrays missing or checkout is incomplete. | Restore the config files before geometry, inference, or losses. |
| `models/shape_predictor_68_face_landmarks.dat` missing | Default dlib landmark path requires an external model not bundled with the checkpoint. | Use bbox-only workflow if a sidecar exists, or obtain the predictor deliberately. |
| CUDA error from `.cuda()` or `torch.cuda.set_device` | Native GPU paths do not auto-fallback. | Verify CPU smokes, then run CUDA-specific checks only on a compatible host. |
| No benchmark data or training filelists | Full training/evaluation depends on external data archives. | Use `training-evaluation` data-layout reference and validate paths before running expensive scripts. |
| C++ build cannot find OpenCV | OpenCV development files are not installed/discoverable by CMake. | Use `cpp-onnx-port` build troubleshooting and install/configure OpenCV >=4.2. |
| C++ demo runs but detects no faces or cannot load weights | Missing ONNX/Yolo weights, wrong working directory, or detector thresholds. | Check C++ weight placement and run/output expectations. |
| PAF fails with `np.int` error | Legacy NumPy alias removed. | Use compatible NumPy or patch alias in a controlled local change. |

## Decision Rules

- Do not treat a passing CPU architecture smoke as proof of native CUDA inference, training, or benchmark extraction.
- Do not treat a missing optional external model as a failed geometry skill; narrow the workflow to bbox/geometry-only or record the missing dependency.
- Do not run full native training, benchmarks, downloads, CMake builds, or GUI/video demos as routine verification. These are explicit user-approved workflows.
- When generated outputs are missing, check whether an earlier artifact was written before a later render/dlib/CUDA exception interrupted the script.

## Sub-skill Owners

- Inference flags, dlib, bbox sidecars, model checkpoint startup: [python-inference troubleshooting](../sub-skills/python-inference/references/troubleshooting.md).
- 3DMM shapes, OBJ/PLY formats, Cython render path, BFM artifacts: [geometry-rendering troubleshooting](../sub-skills/geometry-rendering/references/troubleshooting.md).
- Training filelists, params, CUDA, losses, benchmarks: [training-evaluation troubleshooting](../sub-skills/training-evaluation/references/troubleshooting.md).
- ONNX export, OpenCV/CMake, C++ weights/output: [cpp-onnx-port troubleshooting](../sub-skills/cpp-onnx-port/references/troubleshooting.md).
