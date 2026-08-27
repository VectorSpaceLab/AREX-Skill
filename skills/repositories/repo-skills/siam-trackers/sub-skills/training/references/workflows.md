# Training Workflows

## 1. Define the Run Before Touching CUDA

Collect and record:

- compatible NanoTrack project root;
- copied YAML config and variant identity;
- active dataset names, roots, annotations, and crop provenance;
- seed, target GPU, expected memory budget, and worker count;
- unique log and snapshot directories;
- new run, model-only initialization, or resume;
- single-process or a separately maintained distributed implementation;
- stop criterion and who may terminate a long run.

Use one immutable config copy per run. Relative paths are interpreted from the
launch cwd, so launch from the project root and record it. Avoid output paths
shared with another run.

## 2. Static Configuration Preflight

From any directory, call the bundled checker by absolute skill path:

```bash
python "$SKILL_DIR/scripts/check_training_config.py" \
  --config "$CFG" \
  --project-root "$NANOTRACK_ROOT" \
  --world-size 1 \
  --require-cuda
```

The checker only reads the config and optional paths. It does not import the
project, construct a model, load checkpoints, modify data, or start training.
It merges bundled defaults to expose inherited hazards.

Review all warnings. In particular:

- A geometry heuristic mismatch can be intentional only when supported by the
  selected architecture (V3 is the known case).
- Path checks omitted without `--project-root` are not proof of data readiness.
- Epoch samples not divisible by `batch_size * world_size` can make the loop's
  integer epoch-boundary inference drift from loader batching.
- The checker cannot see implementation-level head selection or channel shapes.

`--strict-warnings` is useful in automation after intentional warnings have
been resolved rather than merely accepted.

## 3. Data Gate

### Gate A: index structure

For every `DATASET.NAMES` entry:

1. Resolve `ROOT` and `ANNO` from the launch root.
2. Require root directory and annotation file to exist and be readable.
3. Inspect one video/track record without rewriting it.
4. Confirm frame keys are six-digit numeric strings.
5. Confirm every sampled box has positive extent.
6. Build the exact crop name `<frame6>.<track>.x.jpg` and require it to decode as
   a three-channel image.

The bundled checker performs steps 1-2 when given `--project-root`; it does not
load a potentially huge annotation file. Steps 3-6 are deliberate operator
probes.

### Gate B: dataset sample

Only after Gate A, import the compatible project in its prepared environment
and construct one `BANDataset` sample with `TRAIN.NUM_WORKERS=0`. Assert:

```text
template: float32, CHW, square side TRAIN.EXEMPLAR_SIZE
search: float32, CHW, square side TRAIN.SEARCH_SIZE
label_cls: integer grid OUTPUT_SIZE x OUTPUT_SIZE
label_loc: float grid 4 x OUTPUT_SIZE x OUTPUT_SIZE
bbox: four finite corners
```

Also require at least one class target not equal to `-1`. For positive-pair
sampling, expect both positive and negative labels when the augmented box is
well formed. A negative pair can legitimately contain zero labels and ignored
positions but no positive labels.

### Gate C: one loader batch

Construct a `DataLoader` using the configured batch and worker count only after
one-sample success. Confirm all four model inputs batch correctly. If the
multi-worker loader fails, return to `NUM_WORKERS=0`; do not hide an annotation
or crop error by retrying the long run.

## 4. CUDA and Environment Gate

The training path is CUDA-only. Before launch:

```bash
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
print("device count:", torch.cuda.device_count())
if torch.cuda.is_available():
    i = torch.cuda.current_device()
    print("device:", i, torch.cuda.get_device_name(i))
    x = torch.ones(1, device="cuda")
    print("allocation:", x.item())
PY
```

Then check device occupancy with the site's GPU monitor and obtain permission
for a free device. `torch.cuda.is_available()` proves neither capacity nor
exclusive access.

Construction-time evidence was limited to an isolated Python 3.13 overlay with
PyTorch `2.13.0+cu130`: a CUDA allocation smoke passed on an A100-class SM80
when a free GPU was explicitly selected, and package consistency passed. This
is evidence that one inspection environment worked, not a version mandate or a
training proof. The historical dependency list targets much older Python,
PyTorch, CUDA, Pillow, Ray, and related packages; treat it as compatibility
history and solve dependencies for the actual driver and hardware.

The evaluation-region native extension is not a training dependency. Its
presence must not be used as evidence that training or evaluation imports work
on a different Python ABI.

## 5. Model and Loss Gate

Before a long run, construct the selected model on the chosen GPU and check a
single forward/backward with a real loader batch. The training model requires:

```text
{
  template,
  search,
  label_cls,
  label_loc
}
```

Its forward path computes backbone features for template and search, invokes
the BAN head, applies log-softmax to classification output, then computes cross
entropy and IoU losses. Require:

- `BAN.BAN=true` and a constructed `ban_head`;
- neck/head/backbone channels match the selected variant;
- `total_loss`, `cls_loss`, and `loc_loss` are scalar and finite;
- backward creates finite gradients on head parameters;
- initially frozen backbone parameters have no gradients unless the configured
  start epoch has reached `BACKBONE.TRAIN_EPOCH`.

Do not use synthetic success to claim the dataset or full run is valid. The
real-batch check is the last bounded gate before launch.

## 6. Safe Single-Process Launch

The source collection's training launcher is a long-running, CUDA/data-bound
entry point with distributed scaffolding but no safe dry-run or max-step flag.
This skill intentionally does not bundle or execute that source launcher. After
the static and real-batch gates pass, an operator who has the selected source
implementation may invoke its documented training entry point from that
checkout, using an explicit config, one selected physical GPU exposed as
logical GPU 0, and an audit directory. Treat the source launcher as an
external execution dependency, not as a runtime file in this skill.

Before any such launch, record the exact config path, selected device, commit,
checkpoint/data fingerprints, and intended log/snapshot destinations. The
training program creates configured log/snapshot output; do not point those
paths at shared results. If the user requested a dry run, stop after the
bundled checker because the historical launcher has no dry-run or max-step
flag.

The default entry-point config filename should not be trusted. Always pass
`--cfg`. Ensure `TRAIN.LOG_DIR` and `TRAIN.SNAPSHOT_DIR` in that exact file are
run-specific. This is a long-running command and must not be started solely to
validate syntax.

## 7. What the Loop Actually Does

Startup order:

1. Seed Python, NumPy, and Torch; set deterministic cuDNN behavior.
2. Initialize the stub distributed state as rank 0/world size 1.
3. Merge YAML and create log directory/file.
4. Construct `ModelBuilder().cuda().train()`.
5. Optionally load `BACKBONE.PRETRAINED`.
6. Open TensorBoard writer on rank 0.
7. Construct `BANDataset` and `DataLoader`.
8. Freeze/unfreeze parameters for the configured start epoch, then build SGD and
   the LR scheduler.
9. Restore a full resume checkpoint, otherwise optionally load model-only
   `TRAIN.PRETRAINED`.
10. Wrap the model in `DistModule` and iterate.

Per batch, the loop computes outputs and examines `total_loss`. If loss is NaN,
infinite, or greater than `1e4`, it silently skips zero-grad/backward/step but
continues timing and logging. Therefore count optimizer progress; visible loop
progress alone is not evidence of learning.

Valid loss triggers zero-grad, backward, gradient reduction (a no-op at world
size 1), optional gradient TensorBoard logging, gradient clipping, and SGD
step. Scalars and timing are added to TensorBoard; text status appears every
`PRINT_FREQ` batches.

Epoch size is inferred as:

```text
num_per_epoch = dataset_length // EPOCH // (BATCH_SIZE * world_size)
```

The dataset length normally equals `VIDEOS_PER_EPOCH * EPOCH`. This explains
why divisibility and nonzero `num_per_epoch` are preflight requirements.

## 8. Optimizer and Scheduler Lifecycle

At optimizer construction:

- all backbone parameters are frozen and backbone BatchNorm is put in eval;
- if `current_epoch >= BACKBONE.TRAIN_EPOCH`, each named layer is unfrozen and
  its BatchNorm is returned to train;
- backbone uses scaled LR;
- enabled neck and BAN head use base LR;
- SGD uses configured momentum and weight decay;
- the LR scheduler is built for `TRAIN.EPOCH` and stepped to
  `TRAIN.START_EPOCH`.

At the exact backbone training epoch, the loop rebuilds both optimizer and
scheduler. This intentionally discards prior optimizer state for the parameter
sets being rebuilt.

## 9. Checkpoint and Resume Workflow

At each detected epoch transition, rank 0 first saves:

```text
checkpoint_e<N>.pth = {
  epoch: N,
  state_dict: model parameters,
  optimizer: optimizer state
}
```

Then the loop checks for completion, potentially activates backbone training,
and steps the scheduler. Consequences:

- `checkpoint_e<N>` represents state at the boundary entering epoch `N`, before
  that transition's scheduler step.
- Scheduler state is not serialized. Set YAML `TRAIN.START_EPOCH` to the
  checkpoint epoch before launch so scheduler construction aligns; restore
  later assigns the checkpoint epoch to this field but that occurs after the
  scheduler was built.
- Keep architecture, head implementation, enabled neck, optimizer grouping,
  batch semantics, and LR schedule identical unless performing an explicit
  migration.
- The checkpoint saved exactly at `BACKBONE.TRAIN_EPOCH` is created before the
  optimizer is rebuilt to include newly trainable backbone layers. It is a
  hazardous resume point. Prefer a checkpoint from the next epoch boundary,
  whose optimizer reflects the post-unfreeze grouping, or implement and verify
  a deliberate optimizer migration.
- `TRAIN.RESUME` takes precedence over `TRAIN.PRETRAINED`. The separate
  `BACKBONE.PRETRAINED` load occurs before resume and is normally overwritten
  by restored model state.
- Loading uses pickle-backed Torch serialization. Only load trusted
  checkpoints.

Resume preflight:

1. Copy the original effective config; change only run output paths and
   `RESUME`, plus `START_EPOCH` if needed to match the checkpoint.
2. Verify checkpoint trust, file readability, recorded epoch, model key overlap,
   and optimizer parameter-group compatibility in an isolated process.
3. Check whether the epoch is the backbone transition hazard.
4. Run the static checker and CUDA/data gates again.
5. Observe restored epoch/LR and the first optimizer step before detaching.

`TRAIN.PRETRAINED` is appropriate only for a new optimizer/schedule. It does not
restore epoch or optimizer.

## 10. Distributed Status and Safe Boundary

The codebase contains `DistributedSampler`, NCCL initialization helpers,
`DistModule`, broadcast, and gradient reduction. However, the stock training
main calls a stub that always returns `(rank=0, world_size=1)` and never selects
a device from local rank. The `--local_rank` argument is parsed but unused.
Launching multiple stock processes can make all of them believe they are rank
0, collide on outputs, duplicate data, and target the same logical GPU.

Do **not** use this against the stock entry point:

```text
torchrun --nproc-per-node=N ...   # unsafe until distributed initialization is maintained
```

A maintained distributed adaptation must first prove all of the following:

- initialize the process group from `RANK`, `WORLD_SIZE`, and `LOCAL_RANK`;
- call `torch.cuda.set_device(local_rank)` before unqualified `.cuda()`;
- report correct rank/world size and ensure only real rank 0 writes outputs;
- use `DistributedSampler` and define epoch reseeding behavior;
- define whether `BATCH_SIZE` is per-rank or global and revalidate epoch math;
- reduce gradients with the intended sum/average semantics (stock defaults to
  sum, not average);
- avoid config/log/snapshot collisions;
- accept the launcher argument spelling used by the installed PyTorch;
- pass a two-rank bounded forward/backward and checkpoint test.

Only after those changes are independently reviewed should an operator use a
site-appropriate `torchrun` template. Designing that adaptation is software
work, not a supported stock launch.

## 11. Monitoring and Stop Conditions

Expected startup evidence:

- merged config appears in logs;
- active dataset names and sample counts are logged;
- model and scheduler descriptions appear;
- first batch produces all three losses;
- output directories are the intended unique paths;
- GPU memory/process identity matches the allocation.

Stop and diagnose when:

- losses are NaN/Inf/greater than `1e4`, even if the loop continues;
- no optimizer steps occur;
- workers repeatedly restart or report missing/corrupt crops;
- CUDA usage appears on an unallocated GPU;
- channel/output shapes fail;
- output files are shared with another process/run;
- epoch/LR after resume differs from the checkpoint plan.

See [troubleshooting.md](troubleshooting.md) for symptom-oriented recovery.
