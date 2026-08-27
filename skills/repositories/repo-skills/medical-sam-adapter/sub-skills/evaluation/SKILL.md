---
name: evaluation
description: "Evaluate Medical SAM Adapter checkpoints through in-training
  validation or the independent val.py path, interpret threshold-averaged
  IoU/Dice, handle REFUGE and multi-class outputs, and diagnose 3D chunking,
  visualization, CUDA, and checkpoint compatibility."
metadata:
  disco-role: operating
disable-model-invocation: true
license: GPL 3.0
---

# Evaluation

Use this route to score a Medical SAM Adapter model, inspect a checkpoint
before loading it, interpret IoU/Dice output, or reduce validation memory. The
canonical graph entry is the [Medical SAM Adapter root](../../SKILL.md). This
route covers both the periodic `validation_sam` call made by `train.py` and the
independent `val.py` command. It does not own optimizer/adaptation choices,
raw dataset layout, or standalone object-aware detector inference.

## Safe route selection

1. Confirm a CUDA-enabled PyTorch runtime and a selected GPU. CUDA is required
   for actual validation: the evaluation code creates `cuda:<gpu_device>`
   tensors and moves the network and batches there. CPU parser/import checks
   are diagnostics only, not a supported evaluation substitute.
2. Route missing files, NIfTI/NRRD/3D shape or dataset-layout questions to
   [data preparation](../data-preparation/SKILL.md). Route model, encoder, and
   adaptation decisions to [training](../training/SKILL.md). Route the
   separately documented detector/box path to
   [MobileSAMv2 inference](../mobile-inference/SKILL.md).
3. Inspect a supplied checkpoint first:

   ```bash
   python scripts/inspect_checkpoint.py --checkpoint /path/to/file.pth
   ```

   The helper is read-only, maps to CPU, prefers `weights_only=True`, does not
   import repository code, and never constructs a model. Read
   [checkpoint schema](references/checkpoint-schema.md) for the result and the
   distributed-prefix decision.
4. Keep the base-model file (`-sam_ckpt`) separate from the trained wrapper
   file (`-weights`). Select matching `-net`, `-encoder`, `-multimask_output`,
   `-image_size`, and adaptation structure before launching `val.py`.
5. Supply a positive integer to `-vis`. The parser default is `None`, but
   `validation_sam` evaluates `ind % args.vis` unconditionally; `-vis 0` also
   fails. Preserve the exact checkpoint, dataset split, device, and output
   policy when comparing runs.

## Choose the workflow

- **Training validation:** `train.py` calls `function.validation_sam` on the
  in-memory network during the first five epochs, at positive `-val_freq`
  intervals, and on the final epoch. It uses the current validation loader and
  writes metrics and optional samples in that run's log/sample directories.
- **Independent evaluation:** `val.py` builds a fresh network, loads the
  wrapper from `-weights`, creates a new timestamped `logs/<exp_name>_*`
  directory, and evaluates the test loader once. It still needs the matching
  `-sam_ckpt`, local data, and CUDA. It is not a source-independent metric
  implementation; it shares the repository loader, preprocessing, decoder,
  and `validation_sam` implementation.
- **Metric interpretation:** read [metrics](references/metrics.md) first.
  Predictions and targets are thresholded at five fixed thresholds and the
  per-threshold IoU/Dice values are averaged; a printed value is not simply a
  0.5-threshold score.
- **3D:** use `-thd True` for slice-wise evaluation of `[B,C,H,W,D]` data and
  `-evl_chunk` to split the depth dimension. `-chunk` controls the MONAI
  training crop, not independent validation. See
  [workflows](references/workflows.md) for remainder and aggregation behavior.

## Exact command shape

`val.py` parses the shared CLI with the exact `-flag` spellings and defaults
listed in [workflows](references/workflows.md). A normal 2D invocation is:

```bash
python val.py -net sam -encoder vit_b -mod sam_adpt \
  -weights /path/to/adapter-wrapper.pth \
  -sam_ckpt /path/to/sam-base.pth \
  -dataset isic -data_path /path/to/data \
  -image_size 256 -out_size 256 -vis 50 -gpu_device 0
```

For REFUGE, use the implemented case-sensitive dataset name and two outputs:

```bash
python val.py -net sam -encoder vit_b -mod sam_adpt \
  -weights /path/to/refuge-wrapper.pth \
  -sam_ckpt /path/to/sam-base.pth \
  -dataset REFUGE -multimask_output 2 -vis 50
```

These commands are templates only: paths, weights, data, and compatibility
must be checked first. Full evaluation is not a preflight and is not started
without the user's real artifacts.

## Critical source behaviors

- Several booleans use `argparse` `type=bool`; a non-empty string such as
  `False` is truthy. Do not assume `-thd False` or `-gpu False` disables a
  feature; omit the option or verify the parsed configuration.
- With original SAM, `multimask_output > 1` causes the validation decoder call
  to request multiple masks. EfficientSAM and MobileSAM explicitly request
  `multimask_output=False` in `validation_sam`, regardless of the shared flag.
- The REFUGE loader returns channel 0 cup and channel 1 disc. `-multimask_output
  2` and two-channel metrics are therefore reported separately; do not collapse
  them into one score. See the channel-order caveat in [metrics](references/metrics.md).
- In a non-`none` `-distributed` mode, `get_network` wraps the model in
  `DataParallel`; `val.py` adds one `module.` prefix to every stored key. The
  saver writes `net.module.state_dict()`, so the expected source checkpoint is
  unprefixed. Do not feed an already-prefixed mapping into this path.

For exact defaults, output paths, metric formulas, checkpoint keys, and
recovery steps, use the four bundled references. Escalate shared environment
issues through the root [troubleshooting route](../../references/troubleshooting.md)
when that root reference is available.
