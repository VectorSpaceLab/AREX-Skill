# DINO troubleshooting and recovery

Treat failures as bounded diagnostics. Do not answer a missing dependency or
bad path by downloading ImageNet, a checkpoint, or a PyTorch hub repository.

## Configuration and data

**`FileNotFoundError` for a list or image**

- Verify `DATA.DATA_PATH` and the two required list files.
- Check that each list path is relative to the data root and includes a label.
- Check RGB readability on a small local sample. Stop if the dataset is absent;
  this skill does not acquire it.

**`NotImplementedError` or a single tensor reaches DINO**

- The source dataset selector supports `cifar10`, `cifar100`, and
  `imagenet2012`, but only the ImageNet branch calls `get_train_dino_transforms`.
- Use `imagenet2012` for the unmodified entrypoints, or write and verify a
  separate adapter that returns two global plus local crops.

**DINO loss chunk/shape errors**

- Count the actual list returned by the dataset.
- Confirm `LOCAL_CROPS_NUMBER + 2` equals that count.
- Confirm each crop batch has the same batch dimension and that the first two
  have the global size. Teacher input must be exactly `images[:2]`.
- Keep same-sized crops consecutive; `MultiCropWrapper` groups consecutive
  widths before calling the backbone.

**Patch or positional embedding shape error**

- Check image/local sizes against `PATCH_SIZE`; test the chosen sizes with the
  model smoke before training.
- The backbone interpolates positional embeddings for different crop sizes,
  but unusual non-square or non-patch-compatible dimensions need a focused
  test rather than an assumption.

## Numerical and model behavior

**NaN or infinite loss**

- Re-run one batch in FP32 without AMP.
- Inspect teacher temperature schedule, normalization, `OUT_DIM`, crop count,
  learning-rate/weight-decay values, and gradient clipping.
- Confirm the teacher is frozen and that student/teacher initial states match.
- Stop a long run on the first non-finite value; do not just increase loss
  scaling or continue from a suspect checkpoint.

**Teacher does not change or receives gradients**

- Check `stop_gradient` on every teacher parameter.
- Check that the EMA loop runs after the student optimizer step and pairs the
  same ordered parameter sets.
- A teacher state change should come from EMA, not `backward()`.

**Last layer or head behavior differs from YAML**

- The entrypoints pass `norm_last_layer=True` for the student and do not
  consistently use `MODEL.NORM_LAST_LAYER`. Treat the YAML field as intent only
  until inspected in the pinned source.
- `FREEZE_LAST_LAYER` uses the source helper to stop gradients for early
  epochs; verify the exact epoch convention before comparing runs.

## Launcher and backend failures

**CPU smoke passes but CUDA fails**

- Record CPU as import/tiny-forward evidence only.
- Probe `paddle.is_compiled_with_cuda()`, select `gpu:0`, allocate a tiny tensor,
  and run a tiny layer. Check the installed Paddle wheel and driver before
  attempting AMP.
- Do not claim GPU training if the CUDA probe fails.

**AMP NaN, unsupported kernel, or scaler failure**

- Remove `-amp` and run a bounded FP32 control.
- Check that the GPU is one of the architectures documented by the repository
  for FP16 AMP (Ampere, Volta, or Turing).
- Re-enable AMP only after finite FP32 loss and a successful CUDA smoke.

**Distributed hang or rank mismatch**

- Stop the bounded job and check `CUDA_VISIBLE_DEVICES`, `-ngpus`, rank/world
  size, NCCL setup, and one process per GPU.
- Confirm every worker constructs `DistributedBatchSampler` after distributed
  initialization. A parser pass is not a distributed pass.
- Test two ranks for one batch before using the eight-GPU shell reference.

## Source defects and checkpoint failures

The inspected source has several probable runtime blockers: single-GPU return
value/logging/variable mismatches; `params_gropus` typo; pretrain/resume use of
an undefined `model`; undefined `scheduler` in the shown loop; and inconsistent
DINO-loss suffixes (`_dino_loss.pdparams`, `._dino_loss.pdparams`,
`_dino_loss.pdprams`).

When one appears:

1. Capture the exact traceback and source commit.
2. Make the smallest patch in a separate, reviewable working copy if patching
   is authorized; never silently alter the runtime skill to imply the source is
   fixed.
3. Run config validation and the synthetic smoke again.
4. For a resume, list actual files and compare model, optimizer, and center
   state keys/shapes. Use a new output directory.
5. If only the model state is available, classify it as initialization rather
   than exact resume.

## Optional porting failures

`load_pytorch_weights.py` imports torch and obtains a model from
`torch.hub`; the inspected environment intentionally lacks torch/timm. If
imports fail, report the optional route as unavailable. Do not install packages,
use network, or claim conversion.

If a local port environment is explicitly approved, first compare named
parameters and buffers. Transpose ordinary 2-D linear weights only when source
and target shapes prove it; preserve convolution, embeddings, and other 2-D
parameters as appropriate. Compare batched Paddle/PyTorch outputs with a
recorded tolerance, then save a new `.pdparams`. A backbone output match does
not validate DINO head, teacher, center, or resume compatibility.
