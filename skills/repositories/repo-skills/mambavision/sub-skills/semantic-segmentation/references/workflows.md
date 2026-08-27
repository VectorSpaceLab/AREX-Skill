# Workflows

This reference turns the published MambaVision ADE20K recipes into safe single-GPU and Slurm command patterns.

## Preconditions

Before launching any command, confirm:

- the pinned OpenMMLab stack is installed: `mmengine==0.10.1`, `mmcv==2.1.0`, `opencv-python-headless`, `mmsegmentation==1.2.2`, `mmdet==3.3.0`, and `mmpretrain==1.2.0`
- a CUDA-enabled PyTorch wheel compatible with the local `mmcv` build is available
- the ADE20K tree exists at `ADEChallengeData2016/images/training`, `ADEChallengeData2016/images/validation`, `ADEChallengeData2016/annotations/training`, and `ADEChallengeData2016/annotations/validation`
- the target project keeps the MambaVision adapter importable before `<openmmlab-train-entrypoint>` or `<openmmlab-test-entrypoint>` builds the config

The target CLI entry points import `mamba_vision` directly, so import failures are usually launch-path problems rather than model-definition problems.

## Single-GPU training

### Tiny

```bash
cd <target-segmentation-project-root>
env CUDA_VISIBLE_DEVICES=0 python <openmmlab-train-entrypoint> \
  <mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-512x512_tiny.py
```

### Small

```bash
cd <target-segmentation-project-root>
env CUDA_VISIBLE_DEVICES=0 python <openmmlab-train-entrypoint> \
  <mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-512x512_small.py
```

### Base

```bash
cd <target-segmentation-project-root>
env CUDA_VISIBLE_DEVICES=0 python <openmmlab-train-entrypoint> \
  <mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-512x512_base.py
```

### L3

```bash
cd <target-segmentation-project-root>
env CUDA_VISIBLE_DEVICES=0 python <openmmlab-train-entrypoint> \
  <mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-640x640_l3_21k.py
```

For a custom ADE20K root, append:

```bash
--cfg-options \
  train_dataloader.dataset.data_root=/datasets/ade20k/ADEChallengeData2016 \
  val_dataloader.dataset.data_root=/datasets/ade20k/ADEChallengeData2016 \
  test_dataloader.dataset.data_root=/datasets/ade20k/ADEChallengeData2016
```

If the GPU is memory-bound, reduce `train_dataloader.batch_size` with `--cfg-options`. Keep the L3 config's no-AMP wrapper unless you have a strong reason to test an alternative.

## Single-GPU evaluation

### Base checkpoint

```bash
cd <target-segmentation-project-root>
env CUDA_VISIBLE_DEVICES=0 python <openmmlab-test-entrypoint> \
  <mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-512x512_base.py \
  /path/to/mamba_vision_160k_ade20k-512x512_base.pth
```

### L3 checkpoint

```bash
cd <target-segmentation-project-root>
env CUDA_VISIBLE_DEVICES=0 python <openmmlab-test-entrypoint> \
  <mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-640x640_l3_21k.py \
  /path/to/mamba_vision_160k_ade20k-640x640_l3_21k.pth
```

To adapt the ADE20K location, use the same `--cfg-options` override block as training.

Expected evaluation output ends with `aAcc`, `mIoU`, and `mAcc` on the validation set. Use the published result table in `configuration.md` as the sanity target: 46.0 / 48.2 / 49.1 / 53.2 mIoU for tiny / small / base / L3.

## Slurm training

The bundled shell launchers are reference-only because they hard-code cluster image, account, partition, and mount placeholders. A safe generic pattern is:

```bash
srun --nodes=2 --ntasks-per-node=8 --gres=gpu:8 \
  bash -lc 'cd <target-segmentation-project-root> && python <openmmlab-train-entrypoint> \
    <mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-512x512_tiny.py \
    --launcher slurm'
```

Swap the config file for `small`, `base`, or `l3` as needed. For the paper's larger runs, keep the same 2-node, 16-GPU shape unless your cluster layout differs.

## Slurm evaluation

```bash
srun --nodes=2 --ntasks-per-node=8 --gres=gpu:8 \
  bash -lc 'cd <target-segmentation-project-root> && python <openmmlab-test-entrypoint> \
    <mambavision-segmentation-config-root>/mamba_vision_160k_ade20k-512x512_base.py \
    /path/to/checkpoint.pth --launcher slurm'
```

Use the L3 config and checkpoint together when evaluating the 640x640 family.

## Bundled command helper

Use the helper to print a safe command string without editing shell scripts by hand:

```bash
python scripts/print_mmseg_command.py train base
python scripts/print_mmseg_command.py test l3 --checkpoint ./checkpoints/mamba_vision_160k_ade20k-640x640_l3_21k.pth
```

The helper validates the tiny/small/base/L3 config id and emits a single-GPU command only.
