# Trainer, launch, solver, checkpoint, and custom-loop APIs

Use this reference when adapting FastReID training code rather than merely
assembling a CLI command. It summarizes the public behavior of FastReID version
`1.3` without requiring a future agent to inspect source files.

## Standard setup flow

The standard training entrypoint performs this sequence:

1. Create `cfg = get_cfg()`.
2. Merge the selected config file.
3. Apply trailing `opts` with `cfg.merge_from_list(args.opts)`.
4. Freeze the config.
5. Call `default_setup(cfg, args)` to set up logging, create `OUTPUT_DIR`, write
   the merged `config.yaml`, log the environment and full config, seed RNGs, and
   enable cuDNN benchmark for non-eval jobs when configured.
6. For eval-only: defrost, set `cfg.MODEL.BACKBONE.PRETRAIN = False`, build the
   model, load `cfg.MODEL.WEIGHTS`, and call `DefaultTrainer.test(cfg, model)`.
7. For training: instantiate `DefaultTrainer(cfg)`, call
   `trainer.resume_or_load(resume=args.resume)`, then `trainer.train()`.

## Key signatures

| API | Signature | Use |
|---|---|---|
| `default_argument_parser` | `default_argument_parser()` | Build the standard train/eval parser. |
| `launch` | `launch(main_func, num_gpus_per_machine, num_machines=1, machine_rank=0, dist_url=None, args=())` | Single-process or distributed process launch. |
| `DefaultTrainer` | `DefaultTrainer(cfg)` | Standard train stack for common FastReID workflows. |
| `DefaultTrainer.test` | `DefaultTrainer.test(cfg, model)` | Evaluate a model on `cfg.DATASETS.TESTS`. |
| `build_optimizer` | `build_optimizer(cfg, model, contiguous=True)` | Build optimizer and contiguous parameter wrapper. |
| `build_lr_scheduler` | `build_lr_scheduler(cfg, optimizer, iters_per_epoch)` | Build LR scheduler dictionary. |
| `Checkpointer` | `Checkpointer(model, save_dir='', save_to_disk=True, **checkpointables)` | Save/load model and optimizer/scheduler state. |

## `launch` behavior

`launch` computes `world_size = num_machines * num_gpus_per_machine`.

- `world_size == 1`: calls `main_func(*args)` in the current process. This can
  be CPU or GPU, depending on `MODEL.DEVICE` and model code.
- `world_size > 1`: spawns `num_gpus_per_machine` worker processes and uses
  NCCL distributed initialization. Each worker asserts CUDA availability, sets
  its local CUDA device, initializes process groups, and then calls
  `main_func(*args)`.
- `dist_url="auto"` is supported only for single-machine multi-GPU jobs.
- For multi-machine jobs, prefer a `tcp://host:port` URL and matching network
  interface environment variables on every machine.

Do not use a CPU-only environment to validate multi-GPU execution. It can
validate parser help and config merge only.

## What `DefaultTrainer(cfg)` builds

The default trainer assumes standard ReID training. It builds components in this
order:

1. Training loader through `build_train_loader(cfg)`.
2. Auto-scaled config values such as `MODEL.HEADS.NUM_CLASSES` when the dataset
   provides class count information.
3. Model through `build_model(cfg)`.
4. Optimizer and parameter wrapper through `build_optimizer(cfg, model)`.
5. Distributed wrapper when `comm.get_world_size() > 1`.
6. `AMPTrainer` if `cfg.SOLVER.AMP.ENABLED`, otherwise `SimpleTrainer`.
7. `iters_per_epoch = len(data_loader.dataset) // cfg.SOLVER.IMS_PER_BATCH`.
8. Scheduler dictionary through `build_lr_scheduler(cfg, optimizer,
   iters_per_epoch)`.
9. `Checkpointer(model, cfg.OUTPUT_DIR, optimizer=optimizer, **scheduler)`.
10. Hooks from `build_hooks()`.

Default hooks include iteration timing, LR scheduling, optional precise BN,
optional layer freeze, evaluation at `TEST.EVAL_PERIOD`, periodic checkpointing
at `SOLVER.CHECKPOINT_PERIOD`, and periodic metric writers.

## Resume and load semantics

`DefaultTrainer.resume_or_load(resume=True)` delegates to `Checkpointer`.

- If `resume=True` and `OUTPUT_DIR/last_checkpoint` exists, the listed
  checkpoint is loaded. Model weights plus checkpointable optimizer/scheduler
  state are restored, and the trainer starts at the next epoch recorded in the
  checkpoint.
- Otherwise the trainer loads `cfg.MODEL.WEIGHTS` as model weights only and
  starts from epoch 0.
- `Checkpointer.load(path)` strips a leading `module.` prefix, logs missing and
  unexpected keys, skips incompatible tensor shapes, and loads only existing
  checkpointable objects.
- `PeriodicCheckpointer` writes periodic `model_####.pth`, `model_best.pth`,
  final `model_final.pth`, and updates `last_checkpoint`.

When debugging resume confusion, inspect `OUTPUT_DIR`, `last_checkpoint`, the
presence of optimizer/scheduler keys in the checkpoint, and whether the command
included `--resume`.

## Solver and scheduler details

`build_optimizer(cfg, model, contiguous=True)` groups parameters with FastReID's
optimizer conventions:

- base learning rate and weight decay from `SOLVER.BASE_LR`,
  `SOLVER.WEIGHT_DECAY`, and `SOLVER.WEIGHT_DECAY_NORM`;
- bias/head learning-rate factors from `SOLVER.BIAS_LR_FACTOR` and
  `SOLVER.HEADS_LR_FACTOR`;
- optional freeze-layer handling when `SOLVER.FREEZE_ITERS > 0`;
- optional gradient clipping from `SOLVER.CLIP_GRADIENTS`;
- optimizer class from `SOLVER.OPT` such as `SGD` or `Adam`.

With `contiguous=True`, the return value is `(optimizer, param_wrapper)`. The
trainer passes both into `SimpleTrainer` or `AMPTrainer`.

`build_lr_scheduler(cfg, optimizer, iters_per_epoch)` returns a dictionary:

- `lr_sched` is a `MultiStepLR` or `CosineAnnealingLR` according to
  `SOLVER.SCHED`.
- `warmup_sched` is present when `SOLVER.WARMUP_ITERS > 0`.
- Scheduler timing is epoch-oriented after converting warmup and delay settings
  with `iters_per_epoch`.

If custom code calls these builders directly, keep the dictionary shape intact
when wiring `Checkpointer` or hooks.

## Metrics writers and logs

Default writer output is controlled by `DefaultTrainer.build_writers()`:

- `CommonMetricPrinter(max_iter)` logs ETA, epoch/iter, losses, timing,
  learning rate, and CUDA memory when available.
- `JSONWriter(OUTPUT_DIR/metrics.json)` appends one JSON object per written
  iteration.
- `TensorboardXWriter(OUTPUT_DIR)` writes TensorBoard event files.

`default_setup` writes the full merged config to `OUTPUT_DIR/config.yaml` before
training. `DefaultTrainer.auto_scale_hyperparams` can write an updated config
when it fills `MODEL.HEADS.NUM_CLASSES` from the dataset.

## Customization extension points

Prefer small overrides before replacing the whole loop:

```python
from fastreid.engine import DefaultTrainer

class MyTrainer(DefaultTrainer):
    @classmethod
    def build_evaluator(cls, cfg, dataset_name, output_dir=None):
        # Return (data_loader, evaluator) for the custom metric/data layout.
        return super().build_evaluator(cfg, dataset_name, output_dir)

    @classmethod
    def build_optimizer(cls, cfg, model):
        # Return the same shape as the base API: (optimizer, param_wrapper).
        return super().build_optimizer(cfg, model)

    def build_writers(self):
        writers = super().build_writers()
        return writers
```

Common override targets:

- `build_train_loader` for a custom sampler or dataset mix.
- `build_test_loader` / `build_evaluator` for new evaluation behavior.
- `build_model` for alternate model construction already registered with the
  config system.
- `build_optimizer` / `build_lr_scheduler` for optimizer or schedule research.
- `build_hooks` for extra hooks; keep evaluation and checkpoint ordering
  deliberate.
- `build_writers` for additional logging destinations.
- `run_step` only when the standard loss/optimizer step is unsuitable.

For significantly different research loops, use the lower-level pattern:

1. Build config, model, train/test loaders, optimizer, and scheduler explicitly.
2. Wrap with `DistributedDataParallel` only when `comm.get_world_size() > 1`.
3. Open `EventStorage(start_iter)`.
4. Iterate epochs and batches, compute loss dictionary, reduce scalars, step
   optimizer, step warmup/main schedulers, run evaluation at the chosen period,
   and save checkpoints with metric state.
5. Return final `DefaultTrainer.test`-style metrics.

When doing this, preserve the safe behaviors that matter: no unwanted backbone
downloads during eval-only, consistent `OUTPUT_DIR`, explicit resume state,
main-process-only writes, and distributed synchronization around evaluation.

## Boundaries with other sub-skills

- Use the configuration sub-skill before changing config semantics or recipe
  inheritance.
- Use the dataset sub-skill before changing loader inputs, sampler assumptions,
  or `FASTREID_DATASETS`.
- Use the modeling sub-skill before changing model builders, feature tensor
  contracts, or checkpoint architecture compatibility.
- Use the deployment/project sub-skill before adapting project-specific train
  scripts or export-time models.
