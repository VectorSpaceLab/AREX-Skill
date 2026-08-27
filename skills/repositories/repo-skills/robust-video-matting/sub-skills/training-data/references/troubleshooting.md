# Training and Data Troubleshooting

## Dataset root is missing or empty

**Symptoms:** `FileNotFoundError`, `os.listdir` failures, or validator errors
for a provided root.

**Recovery:** Use [scripts/rvm_validate_data_layout.py](../scripts/rvm_validate_data_layout.py)
with the same paths you plan to put in `DATA_PATHS`. Fix missing `fgr/`, `pha/`,
background, or JSON paths before launching `train.py`.

## `fgr` and `pha` mismatch

**Symptoms:** datasets initialize but load wrong frames or fail when opening
alpha files.

**Likely cause:** clip names or filenames under `fgr/` and `pha/` do not match.

**Recovery:** For VideoMatte, ensure both roots contain the same clip
directories and frame names. For ImageMatte, ensure alpha filenames exactly
match foreground filenames.

## Relative paths resolve unexpectedly

The default `train_config.py` uses relative examples. Relative paths resolve
from the process working directory, not from the config file location in every
launch setup.

Use absolute paths or launch consistently from the intended training checkout.
Document any relative-path assumption in experiment notes.

## Dataloader exits or machine runs out of CPU memory

The training source comments warn that the default `--num-workers=8` may cause
dataloader failures when memory is insufficient. Retry with fewer workers, such
as `--num-workers 0`, `1`, or `2`, before changing model code.

## CUDA/NCCL initialization fails

`train.py` uses `torch.cuda.device_count()`, multiprocessing spawn, and NCCL. If
no CUDA GPUs are visible, world size can be zero or process-group initialization
will fail.

Recovery:

- Run training only in a CUDA-capable PyTorch environment.
- Check `nvidia-smi` and `torch.cuda.is_available()`.
- Use an unused `--distributed-port` when multiple jobs share a host.
- Do not use CPU-only import checks as proof that `train.py` can run.

## Out of memory

Official training used large data-center machines. For smaller hosts:

- Reduce `--batch-size-per-gpu`.
- Reduce `--resolution-hr` or avoid `--train-hr` during debugging.
- Reduce `--seq-length-lr`/`--seq-length-hr` for experiments, while noting that
  this changes the training recipe.
- Lower `--num-workers` if CPU memory is the issue.

## Pretrained backbone download stalls or fails

`init_model` constructs `MattingNetwork(..., pretrained_backbone=True)`, which
can request TorchVision backbone weights. Prepare cache/network access in
advance, or modify a local experiment intentionally if offline training from
scratch is acceptable. Do not silently remove this behavior when claiming to
reproduce the official recipe.

## Legacy dependency pins conflict with modern Python

The repo's requirement files pin `torch==1.9.0` and `torchvision==0.10.0`.
Those pins are historical evidence for the original release. Modern Python
versions may not have compatible wheels. For inspection and helper scripts, a
modern compatible PyTorch can validate APIs, but full training reproduction
should record any dependency deviation.

## Missing `easing_functions` or TensorBoard

Training imports `easing_functions` for motion augmentation and TensorBoard's
`SummaryWriter` for logging. Install the training requirements or equivalent
packages before launching training.

## Dataset acquisition is blocked

Several datasets are large or require author contact, account access, or manual
preprocessing. Do not script repeated downloads. Record which dataset is
missing, whether it is required for the selected stage, and whether a smaller
local substitute is only for debugging rather than paper reproduction.

## Segmentation data is forgotten

Even matting stages initialize COCO/SPD/YouTubeVIS segmentation datasets for the
segmentation pass. Missing segmentation paths can block training even when the
VideoMatte/ImageMatte roots are correct.
