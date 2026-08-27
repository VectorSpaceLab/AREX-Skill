# Troubleshooting

## Import and install

`config`, `datasets`, `utils`, and model modules are bare top-level imports.
Run from exactly one selected model directory or put only that directory first
on `PYTHONPATH`; print `module.__file__` and restart after a collision. Install
`yacs==0.1.8` and PyYAML in the same interpreter used by the command. Do not
install torch/timm unless doing an explicitly out-of-scope weight conversion.

## YAML and CLI

Run `scripts/check_classification_config.py --config FILE`. Fix malformed
YAML, case-sensitive keys, missing `BASE` files, wrong scalar/list types, and
missing DATA/MODEL sections. A parsed YAML is not proof of model compatibility:
compare it to the selected folder's defaults. Each main parser is local and
usually uses single-dash names (`-cfg`, `-eval`, `-amp`); inspect `--help` and
do not send distillation-only flags to a plain main.

## Data and preprocessing

For missing lists, pass the ImageNet root (not its `train` child) and verify
`train_list.txt`, `val_list.txt`, relative images, integer labels in
`[0,NUM_CLASSES)`, RGB decoding, crop geometry, and one-time normalization.
Set workers to zero while diagnosing loader errors. For ABAW, use aligned
frames/annotation roots and verify the `all`/`coarse`/`negative` mapping instead
of trying ImageNet list files.

## Checkpoints

Inspect whether a file is a plain state dict or bundle with `model`, optimizer,
scheduler, epoch, EMA, and AMP scaler. `-pretrained` is weights-only
finetuning/evaluation; `-resume` is state restoration. When classes change,
replace or omit the old head deliberately. Swin-style models need their
supplied removal of regenerated relative-position/index/mask buffers and
positional embedding interpolation.

## Geometry and backend

A patch/window/stride or positional-embedding mismatch is a model/config issue;
do not silently resize only the tensor. First run the bundled standalone smoke
on CPU; then check `paddle.is_compiled_with_cuda()`, visible devices,
driver/runtime/cuDNN resolution, and run `--device gpu:0`. The prepared evidence
uses Paddle GPU 2.6.2, CUDA 11.8/cuDNN 8.9, and an A100. A bare shell can lack
private NVIDIA loader paths even when the prepared environment is healthy.

If AMP yields non-finite loss, reproduce one batch in FP32, inspect input scale,
then lower batch size/LR before retrying. If distributed execution hangs, prove
one GPU first, match `CUDA_VISIBLE_DEVICES` to process count, use the supplied
sampler/init/DataParallel/barrier sequence, and ensure all ranks share config
and data.

The bundled scripts do not import the original checkout, modify files, load
checkpoints, download data, or train. Their checks are structural/output
contract checks only.
