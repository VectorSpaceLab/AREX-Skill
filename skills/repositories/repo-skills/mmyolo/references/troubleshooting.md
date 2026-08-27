# MMYOLO Cross-Cutting Troubleshooting

Use this reference for failures that happen before a task clearly belongs to one sub-skill.

## Import/version failures

Symptoms:

- `ModuleNotFoundError: No module named 'mmcv'`, `mmengine`, `mmdet`, or `mmyolo`.
- Assertion mentioning incompatible `MMCV`, `MMEngine`, or `MMDetection` versions.
- `mmcv.ops` import errors after installing a mismatched PyTorch/CUDA/MMCV stack.

Recovery:

1. Run `python scripts/check_mmyolo_environment.py --json`.
2. Verify `mmcv>=2.0.0rc4,<2.1.0`, `mmengine>=0.7.1,<1.0.0`, and `mmdet>=3.0.0,<4.0.0`.
3. Use OpenMIM to install the matching OpenMMLab stack rather than mixing arbitrary wheels.
4. If CUDA ops are required, match PyTorch, CUDA runtime, and MMCV wheel tags. CPU MMCV wheels can validate many config/API paths but do not prove CUDA ops.

## OpenCV and augmentation conflicts

Symptoms:

- Image loading/import failures after installing Albumentations.
- Both `opencv-python` and `opencv-python-headless` are present.
- GUI display commands fail on servers.

Recovery:

- Install Albumentations only when the selected config/pipeline needs it.
- Avoid having both GUI and headless OpenCV wheels unless the environment owner accepts the conflict.
- Prefer file-output options such as `--show-dir` or generated output paths over interactive display.

## Config and data mismatch

Symptoms:

- Model still has COCO's 80 classes after changing dataset metadata.
- Evaluator points at a different annotation file than the dataloader.
- TTA asserts about missing `tta_model` or `tta_pipeline`.

Recovery:

- Route config edits to `sub-skills/config-customization/`.
- Route COCO/YOLO/LabelMe/DOTA schema checks to `sub-skills/data-tools/`.
- Validate class metadata, `num_classes`, evaluator `ann_file`, and dataloader `data_prefix` before launching training/evaluation.

## Checkpoints and pretrained weights

Symptoms:

- Missing/unexpected keys during load.
- Head shape mismatch after changing class count.
- Converter output does not match the target MMYOLO config.

Recovery:

- A head mismatch is expected when fine-tuning from COCO weights to a different class count through `load_from`; it is not expected for `resume`.
- Confirm the checkpoint family and converter match the model config.
- Use `sub-skills/deployment-conversion/references/model-converters.md` for upstream YOLO-family key conversion.

## Backend and hardware blocks

Symptoms:

- CUDA unavailable even though the machine has a GPU.
- TensorRT/RKNN/DeepStream package imports fail.
- Deployment export succeeds on ONNX but engine build fails.

Recovery:

- Check whether the requested workflow truly needs the backend. CPU is enough for config/API checks, but not for TensorRT/RKNN/DeepStream proof.
- Run `sub-skills/deployment-conversion/scripts/check_deployment_dependencies.py` for deployment-specific probes.
- Stop early when vendor hardware or packages are unavailable; switch to CPU ONNXRuntime or prepare a backend-capable environment.

## MIM package command issues

Symptoms:

- `mim` command not found.
- `mim train mmyolo --help` or `mim run mmyolo --help` cannot discover commands.

Recovery:

- Install OpenMIM and MMYOLO in the same Python environment.
- Verify package metadata and MIM resources are present by running the help commands.
- Do not launch training, testing, downloads, or deployment as a repair step unless the user explicitly asked for execution.
