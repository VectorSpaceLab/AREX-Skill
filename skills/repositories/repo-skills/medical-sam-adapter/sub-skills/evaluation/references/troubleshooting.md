# Evaluation troubleshooting

## Entry-point and missing-checkpoint errors

- **No metrics are printed:** independent `val.py` only calls
  `validation_sam` when `-mod sam_adpt`. Other mode strings are parsed but do
  not enter the evaluation branch; route mode selection to [training](../../training/).
- **`-weights` is `0`, missing, or does not exist:** `val.py` asserts that a
  weight was supplied and that the file exists. Use a concrete local path.
  Run `scripts/inspect_checkpoint.py --checkpoint ...` first.
- **`KeyError: epoch`, `best_tol`, or `state_dict`:** the file is not the
  wrapper schema expected by independent `val.py`, or is incomplete. A raw
  SAM/EfficientSAM base state dict is not an adapter wrapper; keep it as
  `-sam_ckpt` only when its registry accepts it and find the separate adapter
  wrapper for `-weights`.
- **Load error under `weights_only`:** the file may use unsupported serialized
  objects or be corrupt. Do not disable safety blindly. Confirm provenance,
  use the PyTorch version that produced the artifact if permitted, and inspect
  a copy. The bundled helper refuses legacy arbitrary-pickle loading when the
  installed PyTorch has no `weights_only` support.
- **Base checkpoint prompt/download:** the original SAM builder can prompt for
  certain canonical filenames. Supply an existing, compatible local
  `-sam_ckpt`; evaluation should not depend on an interactive download.

## State-dict prefixes and architecture

- **Missing `module.*` / unexpected `module.*`:** match the loading mode to the
  saved namespace. With `-distributed none`, keys must be unprefixed. With any
  other `-distributed` value, the source wraps the network and prepends one
  `module.` to every stored key. Do not supply keys that already contain that
  prefix to the distributed path.
- **Missing/unexpected keys or size mismatch:** match `-net`, `-encoder`,
  `-image_size`, `-multimask_output`, adaptation structure, and base checkpoint
  to the run that produced the wrapper. Do not “fix” a mismatch by using
  `strict=False`: independent `val.py` uses strict loading and a partial model
  is not a valid evaluation.
- **EfficientSAM/MobileSAM mismatch:** their registries and checkpoint formats
  differ from original SAM. Route model selection to [training](../../training/)
  and inspect the wrapper before launching a run.

## Distributed versus single GPU

- **Distributed run fails at construction or load:** `-distributed` must be a
  comma-separated GPU-id string such as `0,1`, not `True`; make the visible GPU
  numbering and `-gpu_device` consistent. The source uses `DataParallel`, not a
  separate distributed-launch protocol.
- **Single-GPU memory is insufficient:** first try a smaller 2D batch or
  `-evl_chunk` for 3D. Do not change architecture or output channels while
  diagnosing a memory problem. A single-GPU validation with a checkpoint saved
  from a DataParallel run is supported only when the stored keys are
  unprefixed, as produced by this repository's saver.

## Metric interpretation

- **One score expected for REFUGE:** the source returns four values for two
  channels. Report channel 0 cup and channel 1 disc separately; each is an
  average over thresholds 0.1, 0.3, 0.5, 0.7, and 0.9. See
  [metrics](metrics.md).
- **Values differ from another evaluator:** check sigmoid/logit handling,
  five-threshold averaging, the two different epsilons, empty masks, batch
  aggregation, `-out_size`, and whether evaluation was chunked. These are not
  interchangeable protocols.
- **More-than-two-class tuple is confusing:** the order is all IoUs followed
  by all Dice values, channel by channel. The implementation treats channels
  independently; it does not argmax or name classes.
- **Metric tuple length is wrong:** ensure actual decoder channels match
  `-multimask_output`. Original SAM can request multiple masks; EfficientSAM
  and MobileSAM force a single-mask call in `validation_sam`.

## `args.vis`, output directories, and optional visualization

- **`TypeError` involving modulo or `NoneType`:** set `-vis` to a positive
  integer. Despite the parser default `None`, validation evaluates
  `ind % args.vis` unconditionally.
- **Zero/modulo error:** `-vis 0` is invalid; use a positive interval.
- **No `logs/` tree or `FileNotFoundError` while creating it:** run from a
  writable working directory and use a fresh `-exp_name`. The source creates
  `logs/<exp_name>_<timestamp>/{Model,Log,Samples}`. It does not create parent
  directories outside that tree.
- **No sample images:** visualization is interval-controlled by `-vis`, limited
  to four samples per row, and requires `image_meta_dict['filename_or_obj']`
  from the loader. Missing optional torchvision/image dependencies can fail
  visualization even when model metrics are otherwise valid; install/repair
  the selected environment or run a separately reviewed no-visualization
  patch, rather than claiming that `val.py`'s unmodified default is safe.
- **Visualization import error:** this project imports torchvision, PIL,
  matplotlib, MONAI, and related packages at module import. Diagnose the
  environment through the root [troubleshooting](../../../references/troubleshooting.md)
  and do not replace a missing dependency with an unverified API.

## NIfTI/NRRD and 3D chunk errors

- **Missing reader or file:** Brat/KITS/Atlas/SegRap/ToothFairy use NIfTI or
  NumPy conventions; LNQ uses SimpleITK NRRD. Route exact file names,
  orientation, labels, and dataset splits to [data preparation](../../data-preparation/).
  This route does not repair raw data layouts.
- **Shape/rearrange error:** with `-thd True`, the batch must provide image and
  label tensors shaped `[B,C,H,W,D]`. The validation loop converts depth slices
  to `(B*D,C,H,W)`, repeats them to three channels, and uses point prompts
  generated from the volume. A 2D `[B,C,H,W]` batch or a depth mismatch is a
  data-contract error, not a checkpoint error.
- **Lost final slices:** `-evl_chunk N` is processed only while a complete block
  fits. If depth is not divisible by `N`, the source skips the trailing partial
  block. Choose a divisor or report the omission; do not silently pad it.
- **Unexpected aggregate after chunking:** source metrics are accumulated per
  chunk and divided by dataset size, without an additional chunk/slice average.
  Compare chunk policy and depth divisibility before interpreting a change.

## CUDA and memory

- **CUDA unavailable or invalid device:** actual `train.py`/`val.py` workflows
  require CUDA; CPU mode is not a supported substitute. Verify the selected
  device, driver, PyTorch CUDA build, and visible-device numbering through the
  user's environment. Do not report import success as evaluation success.
- **CUDA OOM in 2D:** reduce `-b`, then `-image_size`/`-out_size` only if the
  checkpoint/model contract permits the change. Keep architecture and output
  channels fixed while comparing a checkpoint.
- **CUDA OOM in 3D:** reduce `-evl_chunk` first for independent validation; for
  training, `-chunk`, `-num_sample`, and `-b` belong to the training/data route.
  `-chunk` does not reduce an independent validation block.
- **OOM after changing `-evl_chunk`:** check that the value is positive and
  that the data has a depth dimension. Record the changed aggregation and
  remainder behavior when comparing scores.

## Scope boundaries

Do not use this route for optimizer/adaptation decisions, raw data conversion,
or standalone MobileSAMv2 detector operation. Use
[data preparation](../../data-preparation/), [training](../../training/), and
[mobile inference](../../mobile-inference/) respectively. Escalate cross-route
runtime or publication issues to the root
[troubleshooting](../../../references/troubleshooting.md).
