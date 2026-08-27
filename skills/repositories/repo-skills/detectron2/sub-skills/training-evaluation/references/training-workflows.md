# Training Workflows

## Choose the Driver Shape

Use a project-local Yacs driver that follows Detectron2's standard parser shape for `.yaml` model-zoo configs and ordinary `CfgNode` overrides:

```bash
python PROJECT_TRAIN_DRIVER.py --config-file CONFIG.yaml --num-gpus 1 OUTPUT_DIR output/run MODEL.WEIGHTS weights.pth
```

Use a project-local LazyConfig driver shape for Python config files and object-style overrides:

```bash
python PROJECT_LAZY_TRAIN_DRIVER.py --config-file CONFIG.py --num-gpus 1 train.output_dir=output/run train.init_checkpoint=weights.pth
```

Drivers that use `default_argument_parser` share these flags:

- `--config-file FILE`: path to the config.
- `--resume`: resume optimizer/trainer state from `OUTPUT_DIR/last_checkpoint` when available.
- `--eval-only`: load configured weights/checkpoint and run evaluation only.
- `--num-gpus N`: GPUs per machine; use `1` for single-GPU and `0` only when the chosen script/config is known to support CPU.
- `--num-machines N`, `--machine-rank R`, `--dist-url URL`: multi-machine distributed launch settings.
- trailing `opts`: config overrides; Yacs uses `KEY VALUE`, LazyConfig uses `path.key=value`.

The bundled helper `scripts/train_command_builder.py` emits these command shapes without launching them.

## Yacs Standard Driver Behavior

The standard Yacs driver pattern:

1. Creates `cfg = get_cfg()`.
2. Merges `--config-file` and trailing Yacs `opts` with `cfg.merge_from_file` and `cfg.merge_from_list`.
3. Calls `default_setup(cfg, args)` to create/log `OUTPUT_DIR`, save a config backup, seed RNGs, and configure logging.
4. Launches through `detectron2.engine.launch`.
5. In `--eval-only`, builds a model, calls `DetectionCheckpointer(model, save_dir=cfg.OUTPUT_DIR).resume_or_load(cfg.MODEL.WEIGHTS, resume=args.resume)`, runs `Trainer.test`, optionally runs TTA, and calls `verify_results` on the main process.
6. In training, constructs `Trainer(cfg)`, calls `trainer.resume_or_load(resume=args.resume)`, optionally registers TTA evaluation, then calls `trainer.train()`.

The script's `Trainer` subclasses `DefaultTrainer` and implements `build_evaluator` by inspecting `MetadataCatalog.get(dataset_name).evaluator_type`:

- `coco`: `COCOEvaluator`.
- `sem_seg`: `SemSegEvaluator`.
- `coco_panoptic_seg`: `SemSegEvaluator`, `COCOEvaluator`, and `COCOPanopticEvaluator` wrapped in `DatasetEvaluators`.
- `cityscapes_instance`: `CityscapesInstanceEvaluator`.
- `cityscapes_sem_seg`: `CityscapesSemSegEvaluator`.
- `pascal_voc`: `PascalVOCDetectionEvaluator`.
- `lvis`: `LVISEvaluator`.

For custom projects, copy this pattern into a project script or subclass and manually choose evaluators rather than depending on metadata magic.

## LazyConfig Standard Driver Behavior

The LazyConfig driver pattern:

1. Loads a Python config with `LazyConfig.load(args.config_file)`.
2. Applies trailing overrides with `LazyConfig.apply_overrides(cfg, args.opts)`.
3. Calls `default_setup(cfg, args)`.
4. In `--eval-only`, instantiates `cfg.model`, moves it to `cfg.train.device`, wraps DDP when distributed, loads `cfg.train.init_checkpoint` with `DetectionCheckpointer(model).load`, and calls `do_test`.
5. In training, instantiates `cfg.model`, `cfg.optimizer`, `cfg.dataloader.train`, `cfg.lr_multiplier`, and optional `cfg.dataloader.evaluator`.
6. Uses `AMPTrainer` when `cfg.train.amp.enabled` is true, otherwise `SimpleTrainer`.
7. Registers `IterationTimer`, `LRScheduler`, `PeriodicCheckpointer`, `EvalHook`, and `PeriodicWriter` hooks.

LazyConfig evaluation only runs if `cfg.dataloader.evaluator` exists. If it is missing, add one to the config or run a custom evaluation script.

## `DefaultTrainer` Extension Points

`DefaultTrainer` is useful for standard Detectron2 workflows, but it assumes a single model, optimizer, train loader, LR scheduler, checkpoint directory, and evaluation pattern. It constructs components in this order:

1. `build_model(cfg)` -> `detectron2.modeling.build_model`.
2. `build_optimizer(cfg, model)` -> `detectron2.solver.build_optimizer`.
3. `build_train_loader(cfg)` -> `build_detection_train_loader(cfg)`.
4. DDP wrapper with `create_ddp_model(model, broadcast_buffers=False)` when distributed.
5. `SimpleTrainer` or `AMPTrainer` depending on `cfg.SOLVER.AMP.ENABLED`.
6. `build_lr_scheduler(cfg, optimizer)`.
7. `DetectionCheckpointer(model, cfg.OUTPUT_DIR, trainer=weakref.proxy(self))`.
8. default hooks.

Override classmethods for focused changes:

- `build_evaluator(cls, cfg, dataset_name)`: required for automatic evaluation.
- `build_train_loader(cls, cfg)`: custom mapper/sampler/loader.
- `build_test_loader(cls, cfg, dataset_name)`: custom test loader.
- `build_optimizer(cls, cfg, model)`: custom optimizer or parameter groups.
- `build_lr_scheduler(cls, cfg, optimizer)`: custom scheduler.
- `build_model(cls, cfg)`: custom model construction.
- `build_hooks(self)`: add, remove, or reorder hooks.
- `build_writers(self)`: custom metric writers.

When these assumptions break, switch to `SimpleTrainer`, subclass `TrainerBase`, or adapt a plain PyTorch loop.

## `SimpleTrainer`, Hooks, and EventStorage

`SimpleTrainer(model, data_loader, optimizer, gather_metric_period=1, zero_grad_before_forward=False, async_write_metrics=False)` performs only the basic iterative optimization step: fetch data, call the model, sum losses, zero gradients, backward, step optimizer, and write metrics. Add behavior with hooks:

- `hooks.IterationTimer()`: iteration timing.
- `hooks.LRScheduler(optimizer=None, scheduler=None)`: scheduler stepping and LR logging.
- `hooks.PeriodicCheckpointer(checkpointer, period)`: periodic checkpoint saves.
- `hooks.EvalHook(eval_period, eval_function, eval_after_train=True)`: periodic/final evaluation; function must return nested numeric dicts.
- `hooks.BestCheckpointer(eval_period, checkpointer, val_metric, mode="max")`: save best checkpoint after an eval metric appears in storage.
- `hooks.PeriodicWriter(default_writers(output_dir, max_iter), period=20)`: metrics JSON, TensorBoard, and console output.
- `hooks.PreciseBN(period, model, data_loader, num_iter)`: update BN statistics before evaluation/checkpointing.

Training loops open `EventStorage(start_iter)` while `TrainerBase.train` runs. Calling `get_event_storage()` in model/training code requires this context; outside a trainer, create `with EventStorage(0): ...` or avoid storage calls.

## Solver, Batch Size, and LR Adjustments

For Yacs configs, the important training knobs are:

- `SOLVER.IMS_PER_BATCH`: total images per batch across all workers.
- `SOLVER.BASE_LR`: base learning rate.
- `SOLVER.MAX_ITER`, `SOLVER.STEPS`, `SOLVER.WARMUP_ITERS`: schedule length and milestones.
- `SOLVER.CHECKPOINT_PERIOD`: checkpoint interval.
- `TEST.EVAL_PERIOD`: evaluation interval.
- `MODEL.ROI_HEADS.NUM_CLASSES`: class count for common ROI-head fine-tuning.
- `MODEL.WEIGHTS`: initial weights or checkpoint.
- `OUTPUT_DIR`: logs/checkpoints/config backup.

`DefaultTrainer.auto_scale_workers(cfg, world_size)` only auto-scales when `SOLVER.REFERENCE_WORLD_SIZE` is nonzero and differs from the current world size. It preserves per-GPU batch size and scales total batch, LR, max iteration, warmup, milestones, eval period, and checkpoint period. If not relying on auto-scale, manually scale LR roughly in proportion to total batch size and check schedule length.

A common one-GPU fine-tuning adaptation from an eight-GPU COCO recipe is:

```bash
python PROJECT_TRAIN_DRIVER.py \
  --config-file CONFIG.yaml \
  --num-gpus 1 \
  MODEL.WEIGHTS MODEL_ZOO_OR_LOCAL_WEIGHTS \
  MODEL.ROI_HEADS.NUM_CLASSES 3 \
  DATASETS.TRAIN '("my_train",)' \
  DATASETS.TEST '("my_val",)' \
  SOLVER.IMS_PER_BATCH 2 \
  SOLVER.BASE_LR 0.00025 \
  SOLVER.MAX_ITER 2000 \
  SOLVER.STEPS '(1200, 1600)' \
  TEST.EVAL_PERIOD 200 \
  SOLVER.CHECKPOINT_PERIOD 500 \
  OUTPUT_DIR output/my_run
```

The exact LR/iteration schedule depends on dataset size and model; stop and ask before launching long training or expensive hyperparameter sweeps.

## Resume and Eval-Only Semantics

- `--resume` for training resumes from `OUTPUT_DIR/last_checkpoint` when present and restores trainer/optimizer/scheduler state; otherwise it loads `MODEL.WEIGHTS` and starts at iteration 0.
- Training without `--resume` treats the run as independent and loads only model weights from `MODEL.WEIGHTS`.
- Yacs `--eval-only` builds a model and calls `resume_or_load(cfg.MODEL.WEIGHTS, resume=args.resume)` before `Trainer.test`.
- LazyConfig `--eval-only` loads `cfg.train.init_checkpoint` with `DetectionCheckpointer(model).load`; it does not use Yacs `MODEL.WEIGHTS`.
- Do not combine `--resume` with an intended fresh fine-tune unless the checkpoint directory and `last_checkpoint` are intentionally reused.

## Distributed Launch Safety

`launch(main_func, num_gpus_per_machine, num_machines=1, machine_rank=0, dist_url=None, args=(), timeout=1800)` wraps the job in PyTorch distributed initialization when needed. For multi-machine runs:

- Use the same `--dist-url` on all machines.
- Set unique `--machine-rank` values from `0` to `num-machines - 1`.
- Confirm network reachability and port availability before launching.
- Keep `--num-gpus` as GPUs per machine, not total GPUs.

Stop and ask for explicit user approval before launching multi-GPU or multi-machine jobs.
