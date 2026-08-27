# MMCV Troubleshooting

Use this reference for cross-cutting package and routing failures. For focused failures, route to the nearest sub-skill troubleshooting page.

## Package Variant Confusion

| Symptom | Likely Cause | Next Step |
| --- | --- | --- |
| `import mmcv` works but `import mmcv.ops` fails | `mmcv-lite` or a no-ops source build is installed | Use `sub-skills/ops-and-builds/` and run `scripts/check_mmcv_install.py --require-ops` from that sub-skill. |
| Both `mmcv` and `mmcv-lite` appear installed | Conflicting package variants | Uninstall both, then install exactly one variant for the workflow. |
| A pure image/transform task is blocked on CUDA ops | Wrong route | Use `media-processing` or `data-transforms`; compiled ops are not needed for most lite-safe utilities. |
| A downstream OpenMMLab project reports registry or version errors | Version mismatch or missing module import | Check the downstream project's compatibility table and ensure its modules are imported before blaming MMCV. |

## Optional Dependencies

- Image IO and decoding require image backends such as OpenCV or Pillow. Use headless OpenCV when GUI libraries are unavailable.
- Tensor formatting and `mmcv.cnn` require PyTorch.
- Video editing helpers may require codec/ffmpeg support in the environment.
- Compiled `mmcv.ops` require the full package variant and a compatible PyTorch/CUDA/backend stack.

## Quick Checks

From the root skill directory:

```bash
python scripts/check_mmcv_environment.py --skip-full-ops
```

Use focused helpers when narrowing a failure:

```bash
python sub-skills/media-processing/scripts/media_smoke_check.py
python sub-skills/data-transforms/scripts/transform_pipeline_check.py
python sub-skills/cnn-model-building/scripts/cnn_builder_smoke.py
python sub-skills/ops-and-builds/scripts/check_mmcv_install.py --require-ops
```

## When To Stop

Stop and ask for environment changes when the task requires CUDA/full compiled ops but the current environment has only `mmcv-lite`, CPU-only PyTorch, missing compilers, unsupported CUDA/PyTorch versions, or unavailable hardware. Do not silently rewrite a workflow to avoid ops when the user explicitly needs an op-backed model path.
