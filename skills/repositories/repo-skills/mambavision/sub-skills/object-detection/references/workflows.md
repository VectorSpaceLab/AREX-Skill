# Workflows

This reference covers only the published MMDetection Cascade Mask R-CNN flows for MambaVision. It does not cover generic MMDetection utility folders or unrelated model-conversion tools.

## Preconditions

Before running any command, verify:

- you are inside the target MMDetection project that contains the MambaVision adapter, or `PYTHONPATH` includes that adapter directory
- the OpenMMLab stack from `references/configuration.md` is installed
- the COCO root exists and matches the expected layout
- the backbone checkpoint family matches the selected config family
- the detector checkpoint you pass to evaluation is a full detector checkpoint, not the classification backbone file

The target train/test entry points must import the MambaVision adapter before building the model; that import registers `MM_mamba_vision` into the MMDetection registry.

## Safe command builder

Use `scripts/print_mmdet_command.py` when you need a template command string that stays single-GPU and validates the config id.

Example:

```bash
python scripts/print_mmdet_command.py \
  --mode both \
  --config-id tiny \
  --data-root /path/to/coco \
  --backbone-pretrained /path/to/mambavision_tiny_1k.pth.tar \
  --checkpoint /path/to/cascade_mask_rcnn_mamba_vision_tiny_3x_coco.pth \
  --work-dir ./work_dirs/cascade_mask_rcnn_mamba_vision_tiny_3x_coco
```

If you omit a path, the helper prints a safe placeholder token instead of launching anything.

## Single-GPU training

Use this pattern for quick tests or debugging:

```bash
env CUDA_VISIBLE_DEVICES=0 \
  python <openmmlab-train-entrypoint> \
  <mambavision-detection-config-root>/cascade_mask_rcnn_mamba_vision_tiny_3x_coco.py \
  --work-dir ./work_dirs/cascade_mask_rcnn_mamba_vision_tiny_3x_coco \
  --cfg-options data_root=/path/to/coco \
                  model.backbone.pretrained=/path/to/mambavision_tiny_1k.pth.tar
```

Substitute the config and backbone path for the small or base family when needed.

## Single-GPU testing

Use this pattern for evaluation or regression checks:

```bash
env CUDA_VISIBLE_DEVICES=0 \
  python <openmmlab-test-entrypoint> \
  <mambavision-detection-config-root>/cascade_mask_rcnn_mamba_vision_tiny_3x_coco.py \
  ./work_dirs/cascade_mask_rcnn_mamba_vision_tiny_3x_coco/epoch_36.pth \
  --work-dir ./work_dirs/cascade_mask_rcnn_mamba_vision_tiny_3x_coco/eval \
  --eval bbox segm \
  --cfg-options data_root=/path/to/coco
```

Use `--eval bbox` when you only want box AP, `--eval segm` when you only want mask AP, and `--eval bbox segm` when you want the published instance-detection comparison.

## Slurm training

Use the same config and checkpoint choices, but switch the launcher and let the cluster wrapper provide the site-specific partition, account, and container settings:

```bash
srun --gres=gpu:8 \
  python <openmmlab-train-entrypoint> \
  <mambavision-detection-config-root>/cascade_mask_rcnn_mamba_vision_small_3x_coco.py \
  --launcher slurm \
  --work-dir ./work_dirs/cascade_mask_rcnn_mamba_vision_small_3x_coco \
  --cfg-options data_root=/path/to/coco \
                  model.backbone.pretrained=/path/to/mambavision_small_1k.pth.tar
```

The published shell launchers use the same idea but contain cluster placeholders that you should replace with your own site settings.

## Slurm testing

```bash
srun --gres=gpu:8 \
  python <openmmlab-test-entrypoint> \
  <mambavision-detection-config-root>/cascade_mask_rcnn_mamba_vision_base_3x_coco.py \
  ./work_dirs/cascade_mask_rcnn_mamba_vision_base_3x_coco/epoch_36.pth \
  --launcher slurm \
  --work-dir ./work_dirs/cascade_mask_rcnn_mamba_vision_base_3x_coco/eval \
  --eval bbox segm \
  --cfg-options data_root=/path/to/coco
```

## Expected outputs

A successful run should eventually show COCO evaluation tables with:

- `bbox_mAP` for box detection
- `segm_mAP` for instance segmentation
- the same family-specific numbers listed in `references/configuration.md` for the published results table

Training runs should create logs and checkpoints in the work directory you chose. Test runs should print the COCO summary and write evaluation artifacts only if you asked for them.
