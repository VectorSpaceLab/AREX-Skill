# Training and evaluation troubleshooting

Use this reference when a FastReID train/eval command fails after config and
dataset scope have been selected.

## Missing datasets or empty splits

Symptoms:

- Dataset folder assertion failures.
- Unknown dataset name or registry errors.
- Evaluation produces empty query/gallery behavior or `num_query` mismatches.

Checks:

1. Route to the dataset sub-skill to validate dataset layout and
   `FASTREID_DATASETS`.
2. Confirm `DATASETS.NAMES` for training and `DATASETS.TESTS` for evaluation.
3. Confirm the dataset root contains the expected train/query/gallery splits.
4. Confirm custom dataset registration code is imported before the loader is
   built.
5. For eval-only, remember that a checkpoint alone is insufficient; the test
   dataset must be available.

## CUDA out of memory

Symptoms:

- `CUDA out of memory` during model forward/backward or evaluation.
- OOM appears only during `TEST.FLIP`, AQE, rerank, or high-resolution configs.

Mitigations:

- Reduce `SOLVER.IMS_PER_BATCH` for training and `TEST.IMS_PER_BATCH` for
  evaluation.
- Reduce input size only if the experiment permits it; changing input size can
  change results.
- Set `DATALOADER.NUM_WORKERS 0` or a smaller worker count when host memory is
  also constrained.
- Use `SOLVER.AMP.ENABLED True` for compatible CUDA training; AMP still requires
  CUDA and may not be available in CPU-only environments.
- Disable or postpone `TEST.FLIP.ENABLED`, `TEST.AQE.ENABLED`, or
  `TEST.RERANK.ENABLED` when evaluating memory pressure.
- Confirm `MODEL.DEVICE` points to the intended CUDA device and no stale process
  is holding memory.

## Batch and world-size divisibility

FastReID's train/test batch sizes are global. Per-rank mini-batch is calculated
as:

```text
per_rank_train_batch = SOLVER.IMS_PER_BATCH // world_size
per_rank_test_batch  = TEST.IMS_PER_BATCH // world_size
world_size = num_gpus * num_machines
```

Failure modes:

- Global batch is smaller than `world_size`.
- Global batch is not divisible by `world_size`, so samples per rank are not
  what the user expects.
- Identity samplers have too few samples per rank for
  `DATALOADER.NUM_INSTANCE`.
- `SetReWeightSampler` has additional constraints involving set weights and
  `NUM_INSTANCE`.

Practical fixes:

- Choose `SOLVER.IMS_PER_BATCH` and `TEST.IMS_PER_BATCH` divisible by
  `world_size`.
- For `NaiveIdentitySampler` and `BalancedIdentitySampler`, keep
  `per_rank_train_batch >= DATALOADER.NUM_INSTANCE` and usually divisible by
  `DATALOADER.NUM_INSTANCE`.
- When converting 1-GPU to multi-GPU, decide whether the user wants to preserve
  global batch size or per-GPU batch size; do not silently change both batch and
  learning rate.

## Resume/checkpoint confusion

Symptoms:

- Command supplies `MODEL.WEIGHTS`, but another checkpoint is loaded.
- Training restarts from epoch 0 unexpectedly.
- Eval-only says no checkpoint was found.
- Missing, unexpected, or incorrect-shape keys appear during load.

Decision tree:

1. If the command uses `--resume` and `OUTPUT_DIR/last_checkpoint` exists,
   FastReID loads the checkpoint named there and restores optimizer/scheduler
   states when present.
2. If `--resume` is absent or `last_checkpoint` is absent, training loads
   `MODEL.WEIGHTS` as model weights only and starts from epoch 0.
3. Eval-only always needs `MODEL.WEIGHTS`; `--resume` is not the right mechanism
   for selecting eval weights.
4. Shape mismatches usually mean the checkpoint and config disagree on model
   architecture, embedding/head dimensions, or number of classes.
5. If a checkpoint was saved under distributed training, FastReID strips a
   leading `module.` prefix automatically.

Fixes:

- Set a fresh `OUTPUT_DIR` for new independent runs.
- Keep the same `OUTPUT_DIR` and pass `--resume` for interrupted training.
- Pass `MODEL.WEIGHTS <CHECKPOINT_FILE.pth>` for eval-only and fine-tuning.
- Verify model config compatibility before treating missing/unexpected keys as
  harmless.

## `OUTPUT_DIR/config.yaml` surprises

`default_setup` writes the merged config to `OUTPUT_DIR/config.yaml` at job
startup. `DefaultTrainer.auto_scale_hyperparams` can later update it when it
fills `MODEL.HEADS.NUM_CLASSES` from the dataset.

If `config.yaml` does not match the command you expected:

- Check that trailing `opts` were after all named flags.
- Check shell quoting for tuples, booleans, and paths.
- Check that the run used the intended `OUTPUT_DIR`.
- Remember that resume uses checkpoint state; config differences do not rewrite
  optimizer/scheduler state already stored in a checkpoint.

## Python rank fallback warning

Warning pattern:

```text
Cython rank evaluation ... is unavailable, now use python evaluation.
```

Meaning:

- FastReID could not import the optional Cython rank extension.
- Evaluation falls back to Python implementation.
- Metrics remain meaningful, but large evaluations can be slower.

If speed is required and the user controls the environment, compile the optional
rank extension in that environment. Do not make compilation a prerequisite for
small parser/config/model checks.

## Distributed launch failures

Symptoms:

- `cuda is not available` assertion from a distributed worker.
- NCCL timeout or connection failure.
- Port already in use.
- Only some machines start or ranks disagree.

Checks:

1. `--num-gpus * --num-machines` must be greater than 1 only in a CUDA-capable
   environment.
2. Every machine must use the same `--num-machines`, `--num-gpus`, and
   `--dist-url`.
3. `--machine-rank` must be unique per machine.
4. For multi-machine, prefer `tcp://<rank0_host>:<port>` and set matching
   network interface variables when needed.
5. `dist-url=auto` is single-machine only.
6. Dataset and output paths should be shared or consistently mapped across
   machines.

## Eval-only pretrain and download confusion

Eval-only should use the trained checkpoint, not ImageNet pretrain weights.
FastReID's standard eval branch sets `MODEL.BACKBONE.PRETRAIN = False` before
building the model. Still include `MODEL.BACKBONE.PRETRAIN False` in offline
command templates for clarity, and always pass a local `MODEL.WEIGHTS`.

If a command attempts to download weights during a supposed eval-only workflow,
check whether:

- `--eval-only` was omitted;
- a custom entrypoint did not disable pretraining;
- the config sets another pretrained path that the model builder tries to
  resolve;
- the command is actually a model-construction smoke rather than eval-only.

## Stale tests and legacy imports

Some older repo tests/examples in this version are not safe as verification
commands. Known hazards include:

- old import paths such as importing `solver` or `data` as top-level packages
  instead of `fastreid.solver` or `fastreid.data`;
- scripts that enter debuggers or assume local checkpoints;
- visualization code that imports `evaluate_rank` from the top-level evaluation
  package even though the working import is `fastreid.evaluation.rank.evaluate_rank`;
- optional deployment imports such as ONNX, TensorRT, or Caffe that are not part
  of base training/evaluation.

Prefer canonical package imports and the bundled safe scripts for parser/config
checks. Do not treat stale test failures as proof that the standard training CLI
is broken without isolating the import mismatch.
