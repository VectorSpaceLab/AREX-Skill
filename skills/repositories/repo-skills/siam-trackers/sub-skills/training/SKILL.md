---
name: training
description: "Plan, validate, launch, monitor, and safely resume NanoTrack
  training with explicit data, configuration, CUDA, and runtime gates."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# NanoTrack Training

## Scope

Use this operating skill for NanoTrack training requests in the SiamTrackers
collection: preparing cropped training data, editing a copied YAML config,
validating model/data compatibility, selecting a safe launch, interpreting
loss and checkpoint behavior, or planning recovery from a failed run.

NanoTrack is the maintained end-to-end workflow represented here. Treat other
tracker directories as historical snapshots unless another skill says
otherwise.

Route these requests instead:

- Tracking initialization, `template`/`track`, and frame-by-frame use:
  **inference**.
- Benchmark result production or metric interpretation: **evaluation**.
- ONNX, mobile conversion, FLOPs, latency, or deployment: **export**.
- Differences in V1/V2/V3 code selection or training another snapshot:
  **variant-catalog**.

## Hard Limits

- Training is CUDA-only in the stock control flow. It constructs the model with
  `.cuda()` and moves all four training tensors with `.cuda()`; `CUDA: false`
  does not create a CPU training path.
- The stock entry point initializes `rank=0, world_size=1` through a stub.
  Distributed classes are present, but stock multi-process training is not
  enabled. Do not put the unmodified entry point behind `torchrun`.
- A real run needs cropped images, an annotation JSON, compatible weights when
  configured, and substantial time. None is bundled with this skill.
- No full data, training, checkpoint-resume, metric, or export run was verified
  during skill construction. Never promise an accuracy, duration, or output.
- Historical dependency pins describe an old environment. Do not reproduce
  those versions blindly on modern Python/CUDA.

## Operating Sequence

1. Establish a NanoTrack-compatible project root, copied config path, requested
   variant, data ownership, GPU allocation, run directory, and completion
   criterion. Keep every relative config path anchored to the launch root.
2. If the request changes V1/V2/V3 architecture or head selection, consult
   **variant-catalog** first. A YAML filename alone does not select every
   variant-specific implementation detail.
3. Read [configuration.md](references/configuration.md). Confirm `BAN.BAN`,
   backbone/adjust/head channels, training geometry, enabled dataset records,
   augmentation rates, target counts, scheduler, and output paths.
4. Run the bundled read-only checker before importing the training package:

   ```bash
   SKILL_DIR=/path/to/this/training
   python "$SKILL_DIR/scripts/check_training_config.py" \
     --config "$CFG" \
     --project-root "$NANOTRACK_ROOT" \
     --world-size 1 \
     --require-cuda
   ```

5. Treat every checker error as a launch blocker. Review warnings manually;
   geometry warnings can be intentional for a matched variant, but unchecked
   files and non-divisible epoch sizing need explicit acceptance.
6. Perform the data and CUDA gates in
   [workflows.md](references/workflows.md). In particular, probe one annotation
   record and its exact crop file, then load one `BANDataset` sample before a
   long run. Do not use a benchmark dataset layout as a training crop layout.
7. Start with single-process execution and a unique copied config. Set
   `TRAIN.LOG_DIR` and `TRAIN.SNAPSHOT_DIR` to run-specific locations. Use an
   explicitly selected free GPU; an available GPU is not necessarily idle.
8. Watch startup through config merge, model creation, data indexing, first
   forward/backward, first scalar write, and first periodic log. Stop on silent
   invalid-loss skipping, repeated worker failures, or unexpected output-path
   reuse.
9. Resume only after matching the config, variant, optimizer parameter groups,
   and checkpoint epoch. Read the transition-epoch warning in
   [workflows.md](references/workflows.md); scheduler state is reconstructed,
   not restored.
10. Record the exact config, command, environment probe, data identity, seed,
    GPU assignment, and accepted warnings with the run outputs.

## Input Contract

The dataset returns a mapping containing:

| Key | Meaning |
| --- | --- |
| `template` | Float32 CHW crop, normally `3 x TRAIN.EXEMPLAR_SIZE x TRAIN.EXEMPLAR_SIZE` |
| `search` | Float32 CHW crop, normally `3 x TRAIN.SEARCH_SIZE x TRAIN.SEARCH_SIZE` |
| `label_cls` | Int64 point labels: `-1` ignored, `0` negative, `1` positive |
| `label_loc` | Float32 `4 x OUTPUT_SIZE x OUTPUT_SIZE` left/top/right/bottom distances |
| `bbox` | Augmented search-box corners; returned for inspection, not consumed by the model loss |

The training `forward` consumes the first four keys, moves them to CUDA, and
returns `total_loss`, `cls_loss`, and `loc_loss`. The weighted total is:

```text
total_loss = TRAIN.CLS_WEIGHT * cls_loss
           + TRAIN.LOC_WEIGHT * loc_loss
```

The loader uses `TRAIN.BATCH_SIZE`, `TRAIN.NUM_WORKERS`, pinned memory, and an
internally shuffled index list. It does not pass `shuffle=True` to the
`DataLoader`.

## Dataset Gate

For each name in `DATASET.NAMES`, require a non-empty `ROOT`, `ANNO`,
`FRAME_RANGE`, and `NUM_USE`. Relative paths resolve from the NanoTrack launch
root. The maintained GOT record defaults to:

```text
ROOT: data/GOT-10k/crop511
ANNO: data/GOT-10k/train.json
```

A crop is addressed as:

```text
ROOT/<video>/<six-digit-frame>.<track>.x.jpg
```

The annotation must map video to track to six-digit frame keys and valid boxes.
Read the exact schema and sampling behavior in
[configuration.md](references/configuration.md).

## Safe Single-Process Launch

The historical training launcher is a long-running, CUDA/data-bound source
entry point. This skill intentionally does not bundle or execute it. After the
static and real-batch gates pass, an operator with the selected source
implementation may invoke its documented launcher from that checkout using an
explicit config, a selected physical GPU exposed as logical device 0, and
run-specific log/snapshot paths. The source launcher is an external execution
dependency, not a runtime file in this skill.

This command starts a long-running job and must be approved after the gates
pass. Use the bundled checker for dry-run/config validation; the historical
launcher has no safe dry-run or max-step option.

## Output Contract

Rank 0 creates `TRAIN.LOG_DIR`, writes `logs.txt`, and opens a TensorBoard
writer there. It creates `TRAIN.SNAPSHOT_DIR` and saves
`checkpoint_e<N>.pth` at epoch transitions with:

- `epoch`
- `state_dict`
- `optimizer`

The scheduler is absent from the checkpoint. `TRAIN.RESUME` restores model,
optimizer, and epoch; `TRAIN.PRETRAINED` loads model weights only and is ignored
when resume is set. `BACKBONE.PRETRAINED`, when non-empty, is loaded earlier.

## Failure Routing

Use [troubleshooting.md](references/troubleshooting.md) for missing crops,
annotation schema failures, worker crashes, CUDA/OOM errors, geometry or channel
mismatches, invalid losses, scheduler/resume issues, and unsafe distributed
launches. Escalate architecture-selection uncertainty to **variant-catalog**;
do not repair it by guessing channels or output sizes.
