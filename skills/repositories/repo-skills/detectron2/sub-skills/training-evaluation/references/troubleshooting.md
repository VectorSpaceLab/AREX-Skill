# Training and Evaluation Troubleshooting

## Stop Conditions

Stop and ask the user before proceeding when:

- A command would start long training, full-dataset evaluation, multi-GPU launch, or multi-machine launch.
- Required data registration, annotation files, image roots, checkpoint files, or hardware are missing.
- The requested run depends on private paths, credentials, unavailable GPUs, or unclear output overwrites.
- A config uses a custom project extension that has not been imported/registered.

## GPU Count, Batch, and LR Mismatch

Symptoms:

- Out-of-memory errors after reducing GPU count or increasing image size.
- Slower or unstable convergence after moving from an 8-GPU recipe to 1 GPU.
- Unexpected auto-scaled iteration counts or LR.

Checks and fixes:

- Confirm `--num-gpus` is GPUs per machine.
- For Yacs, inspect `SOLVER.REFERENCE_WORLD_SIZE`; if nonzero, `DefaultTrainer.auto_scale_workers` may change batch, LR, iterations, warmup, milestones, eval period, and checkpoint period.
- Keep `SOLVER.IMS_PER_BATCH` feasible for hardware; reduce it before reducing image size or model complexity.
- Scale `SOLVER.BASE_LR` roughly with total batch size when not using auto-scale.
- Revisit `SOLVER.MAX_ITER`, `SOLVER.STEPS`, `TEST.EVAL_PERIOD`, and `SOLVER.CHECKPOINT_PERIOD` after changing batch/GPU count.

## Yacs vs LazyConfig Override Syntax

Yacs `.yaml` configs use space-separated key/value pairs:

```bash
MODEL.ROI_HEADS.NUM_CLASSES 3 SOLVER.BASE_LR 0.00025 OUTPUT_DIR output/run
```

LazyConfig `.py` configs use equals syntax:

```bash
model.roi_heads.num_classes=3 optimizer.lr=0.00025 train.output_dir=output/run
```

Do not mix the syntaxes. A common failure is using `KEY VALUE` pairs with `lazyconfig_train_net.py` or `path.key=value` with `train_net.py`.

## Unregistered Dataset

Symptoms:

- `KeyError` or catalog lookup failures for a dataset name.
- `DefaultTrainer.test` cannot build a test loader.
- Evaluator metadata such as `evaluator_type` or `json_file` is missing.

Checks and fixes:

- Confirm the dataset registration code ran in the same process before training/evaluation.
- Verify `DATASETS.TRAIN` and `DATASETS.TEST` contain registered names, including trailing comma tuple syntax for one-element Yacs tuples: `("my_val",)`.
- For COCO-style datasets, ensure metadata includes `json_file` or pass an evaluator `output_dir` so conversion can be written.
- If using custom data, consult the dataset registration sub-skill; do not invent dataset paths.

## Incompatible Pretrained Head Shapes

Symptoms:

- Missing/unexpected key warnings for ROI heads or mask/keypoint heads.
- Shape mismatch when changing number of classes.
- COCO evaluator assertion that predicted class id exceeds dataset class count.

Checks and fixes:

- Set `MODEL.ROI_HEADS.NUM_CLASSES` to the custom dataset class count for common ROI-head models.
- Use a fresh fine-tune rather than `--resume` when class count changes.
- Expect classifier/regressor head weights from a COCO checkpoint not to load exactly; verify the new heads are initialized for the custom class count.
- Confirm dataset metadata class names and contiguous id mapping match the configured class count.

## Missing Checkpoint or Weights

Symptoms:

- `FileNotFoundError`, `OSError`, or empty eval results before inference starts.
- Eval-only unexpectedly loads a previous run checkpoint.
- LazyConfig eval-only uses no weights or the wrong weights.

Checks and fixes:

- For Yacs eval/training, set `MODEL.WEIGHTS` unless intentionally resuming from `OUTPUT_DIR/last_checkpoint`.
- For LazyConfig, set `train.init_checkpoint`; `MODEL.WEIGHTS` is not the LazyConfig field.
- Use `--resume` only with the intended `OUTPUT_DIR` and `last_checkpoint`.
- Check whether a path includes `?matching_heuristics=True`; use it only for legacy alignment cases.

## Resume vs Eval-Only Confusion

- `--resume` controls checkpoint directory resume behavior.
- `--eval-only` chooses evaluation instead of training.
- `--eval-only --resume` can evaluate the checkpoint referenced by `OUTPUT_DIR/last_checkpoint` instead of the explicit weight path.
- For a clean evaluation of a specific checkpoint, use a clear checkpoint path and omit `--resume` unless resuming is intentional.

## Distributed URL and Rank Mistakes

Symptoms:

- Job hangs at startup.
- Workers cannot join the process group.
- Multiple jobs conflict on the same port.

Checks and fixes:

- Use one reachable `--dist-url` for all machines.
- Use unique `--machine-rank` values.
- Set `--num-machines` identically on all machines.
- Avoid reusing a busy `tcp://host:port`.
- Ask for infrastructure details before trying to fix multi-machine failures.

## Long Training and Benchmark Safety

- Treat training and full evaluation as potentially expensive side effects.
- Prefer command builders, config inspection, and small smoke tests before launching full jobs.
- Ask for approval before running commands that will allocate GPUs, download large checkpoints/datasets, write large outputs, or run for a long time.
- For quick validation, lower `SOLVER.MAX_ITER`, use tiny registered datasets, and write to a scratch `OUTPUT_DIR` only with user consent.

## EventStorage Missing

Symptoms:

- `get_event_storage()` raises because no storage context exists.
- Custom model/loss code logs metrics outside trainer execution.

Checks and fixes:

- Metrics logging through `get_event_storage()` works during `TrainerBase.train`, which opens `EventStorage(start_iter)`.
- For isolated tests of metric-writing code, wrap calls in `with EventStorage(0):`.
- For inference/evaluation-only code, avoid training-only storage logging unless explicitly creating a storage context.

## Eval-Only Failure: Unregistered Dataset and Missing Checkpoint

Diagnose in this order:

1. Confirm config style and command syntax are correct.
2. Confirm the dataset names in `DATASETS.TEST` or `cfg.dataloader.test` are registered before the eval command starts.
3. Confirm evaluator type and metadata are available.
4. Confirm checkpoint field: Yacs `MODEL.WEIGHTS`, LazyConfig `train.init_checkpoint`.
5. Confirm `--resume` is not redirecting to an unintended or absent `last_checkpoint`.
6. Stop and ask for dataset registration code or checkpoint location if either is unavailable.
