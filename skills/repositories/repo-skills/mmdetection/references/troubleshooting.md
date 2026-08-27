# Cross-Cutting Troubleshooting

Use this reference for install/import/backend issues before opening workflow-specific troubleshooting.

## Fast Diagnosis

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: mmcv._ext` | `mmcv-lite` is installed or full `mmcv` wheel does not match `torch`/CUDA/Python | Install full `mmcv>=2.0.0rc4,<2.2.0` from an OpenMMLab-compatible wheel index for the active `torch` and backend. |
| `AssertionError: MMCV==... is incompatible` | `mmdet/__init__.py` enforces `mmcv>=2.0.0rc4,<2.2.0` | Pin `mmcv` into the supported range; avoid silently upgrading to newer MMCV major/minor lines. |
| `AssertionError: MMEngine==... is incompatible` | MMEngine outside `>=0.7.1,<1.0.0` | Install a compatible `mmengine` version and rerun import checks. |
| Torch imports warn about NumPy ABI or fail in compiled extensions | Binary wheels were compiled against NumPy 1.x but NumPy 2.x is installed | Pin `numpy<2` and use OpenCV/MMCV/Torch wheels compatible with that ABI, or move the entire stack to wheels built for NumPy 2. |
| OpenCV requires NumPy 2 but Torch/MMCV need NumPy 1.x | Mixed new OpenCV with older compiled ML stack | Use an older compatible `opencv-python`/`opencv-python-headless` wheel or upgrade the whole stack together. |
| CPU inference fails with RoIPool assertion | The model contains RoIPool, which MMDetection blocks on CPU inference | Use a GPU-capable environment or choose a config without RoIPool for CPU checks. |
| `show=True` fails on a server | No GUI/display server | Save outputs to a directory and disable popup display. |
| Model name download stalls or fails | MIM/model-zoo download needs network | Use local config/checkpoint paths or download artifacts out of band. |
| Checkpoint labels are wrong | Checkpoint metadata, config dataset metainfo, and target classes disagree | Align config, dataset metainfo, `num_classes`, evaluator annotations, and checkpoint choice. |
| Custom type not found in registry | Module was not imported or default scope is wrong | Use `customization-extension` and the registry probe helper to verify imports and registry ownership. |

## Minimal Import Probe

Run the root checker first:

```bash
python scripts/check_mmdet_environment.py
```

It should report versions and signatures for `DetInferencer`, `init_detector`, and `inference_detector`. If this fails, fix imports before debugging model configs or datasets.

## Install Strategy Notes

- Prefer documented OpenMMLab install paths for `mmcv` because it contains compiled ops tied to `torch`, Python, CPU/CUDA, and platform tags.
- Do not use `mmcv-lite` for workflows that import detection structures, masks, datasets, or inference APIs relying on `mmcv.ops`.
- For CPU-only troubleshooting, install CPU `torch` and a CPU-compatible full `mmcv`; GPU-specific performance and kernels are not verified by CPU imports.
- For CUDA workflows, match the NVIDIA driver, `torch` CUDA wheel, and `mmcv` CUDA wheel. A GPU being present does not prove the wheel stack is compatible.
- Avoid broad optional extras unless the requested workflow needs them: tracking, multimodal, docs, tests, and deployment dependencies can introduce unrelated conflicts.

## Workflow-Specific Routing

- Config import, `_base_`, model names, and checkpoint/config pairing: `sub-skills/configuration-model-zoo/references/troubleshooting.md`.
- Inference, visualization, output files, text prompts, deployment route selection: `sub-skills/inference-visualization/references/troubleshooting.md`.
- Training, resume, distributed launch, testing, Slurm, `work_dir`: `sub-skills/training-testing/references/troubleshooting.md`.
- Dataset schemas, class/category mapping, transforms, metrics: `sub-skills/datasets-evaluation/references/troubleshooting.md`.
- Registries, `custom_imports`, custom modules, migration: `sub-skills/customization-extension/references/troubleshooting.md`.
