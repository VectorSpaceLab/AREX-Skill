---
name: ops-and-builds
description: "Choose MMCV package variants, inspect compiled ops availability,
  and troubleshoot install, build, CUDA, and backend failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMCV Ops And Builds

Use this sub-skill when a task involves installing MMCV, deciding between `mmcv` and `mmcv-lite`, checking whether compiled `mmcv.ops` are available, selecting a wheel or source build, or diagnosing native-extension/CUDA/backend errors.

## Route Here

- The user needs NMS, ROI/rotated ROI pooling, deformable convolution, sparse convolution, 3D/point-cloud ops, attention kernels, focal losses, or other `mmcv.ops` APIs.
- The user reports `No module named mmcv.ops`, `No module named mmcv._ext`, shared-object load errors, undefined symbols, CUDA kernel errors, or build failures.
- The user asks which package to install for CPU-only, CUDA, MLU, MUSA, NPU, MPS, or lite/no-ops workflows.
- The user needs verification commands after installing or building MMCV.

## Route Elsewhere

- Pure image/video/visualization utilities belong in `../media-processing/`.
- Data transform pipelines belong in `../data-transforms/`.
- CNN layer builders that do not require compiled `mmcv.ops` belong in `../cnn-model-building/`.

## Start With Package Selection

1. Use `mmcv-lite` when the workflow does not import `mmcv.ops` and does not need compiled native kernels.
2. Use full `mmcv` when any compiled op is required; in MMCV 2.x, `mmcv` is the full package and `mmcv-lite` is the lite package.
3. Do not install both packages in one environment. If switching variants, uninstall the other variant first.
4. Treat compiled ops as conditional: successful `import mmcv` does not prove that `mmcv.ops` or `mmcv._ext` exists.

## Key References

- Read [references/install-and-build.md](references/install-and-build.md) for package choice, MIM/pip/source-build flows, environment variables, compatibility checks, and verification commands.
- Read [references/ops-reference.md](references/ops-reference.md) for ops families, representative APIs, and backend support cautions.
- Read [references/troubleshooting.md](references/troubleshooting.md) for symptom-to-cause recovery guidance.
- Run [scripts/check_mmcv_install.py](scripts/check_mmcv_install.py) to inspect installed package facts without relying on the original checkout.

## Diagnostic Commands

```bash
python scripts/check_mmcv_install.py
python scripts/check_mmcv_install.py --require-ops
python scripts/check_mmcv_install.py --require-cuda --require-ops
```

The checker reports import/package/Torch/CUDA facts, handles missing ops gracefully, and exits nonzero only when a required check fails.
