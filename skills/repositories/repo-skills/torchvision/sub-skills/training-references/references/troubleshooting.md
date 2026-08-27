# Training reference troubleshooting

## Latest-source script and stable package mismatch

TorchVision reference scripts are not stable public APIs. They can use the latest source package behavior and may fail with older installed `torch` or `torchvision` versions. If a user needs reproducibility, use reference scripts from the same release tag as the installed package, and keep command guidance version-qualified.

Symptoms include unknown model names, missing weight enums, changed transform flags, missing `--use-v2`, import failures from local helper modules, or different default preprocessing. Route model and weight enum questions to `../models-and-weights/`.

## Missing datasets

Most recipes assume full datasets already exist locally. Do not suggest automatic downloads for ImageNet, COCO, Kinetics, FlyingThings, Sintel, KITTI, Middlebury, or similar large datasets unless the user explicitly asks and accepts network/storage cost.

Before running evaluation or training, confirm:

- The data root exists and contains expected train/validation splits.
- Annotation JSON files exist for COCO detection, segmentation, or keypoints.
- Video files are readable and codecs are installed for Kinetics-style data.
- Flow/stereo roots contain the selected dataset family names and annotation/ground-truth files.
- Calibration data exists for post-training quantization.

## Distributed launch failures

Common failures are caused by copying `--nproc_per_node=8` onto a machine with fewer GPUs, launching `torchrun` from the wrong working directory, unset rendezvous variables for multi-node runs, or using `--sync-bn` on CPU.

Safer alternatives:

- Convert a reproduction command into a plan rather than running it.
- For evaluation-only checks, prefer `python train.py --test-only ...` when the script supports it.
- Set `--nproc_per_node` to the actual local GPU count.
- Avoid multi-node flags unless the user provides cluster details.

## GPU and CPU expectations

Classification, detection, segmentation, video, optical flow, and stereo training are GPU-oriented and often benchmarked on many V100 or A100 GPUs. CPU runs may be impractically slow. Post-training quantization can be CPU-oriented, but still needs calibration/evaluation data and backend selection such as `fbgemm` or `qnnpack`.

Warn users before enabling `--amp`, `--sync-bn`, large `--batch-size`, `--cache-dataset`, or video clip settings. These options can fail or exhaust memory on smaller machines.

## COCO, video, flow, and stereo layouts

COCO tasks require matching `--dataset` values to annotations: `coco` for boxes/masks and `coco_kp` for keypoints. Video classification expects Kinetics-style train/validation videos and can require hundreds of GB. Optical flow and stereo datasets use specialized layouts; a generic image folder will not work.

For stereo, also verify that dataset-step lists match dataset lists and that crop/resize/scale/max-disparity choices match the target data domain. Stereo reference material may depend on removed prototype-era code and should be marked fragile.

## Checkpoints and weights misuse

Do not mix `--resume` or `--resume-path` with `--weights` casually:

- `--weights` selects model initialization or evaluation weights from a weight enum.
- `--weights-backbone` initializes only a backbone where supported.
- `--resume` usually restores a training checkpoint and optimizer/scheduler state.
- `--resume-path` in stereo references is a script-specific checkpoint path.

For classification evaluation, prefer weight enums and their preprocessing transforms over deprecated `pretrained=True`. If a weight name is unknown, inspect installed models/weights with `../models-and-weights/` rather than guessing.

## Long-running commands

Any command with `torchrun`, multiple epochs, large datasets, video clips, optical-flow/stereo training, or quantization-aware training is unsafe by default. Provide dry-run-safe plans, required assumptions, expected resources, and exit criteria before running.

Excluded from this sub-skill's runtime guidance:

- Release automation and maintainer scripts.
- Model URL collection/download scripts that perform network-heavy cache checks.
- Preprocessing benchmarks such as `preprocess-bench.py`, which are performance tests rather than training references.
