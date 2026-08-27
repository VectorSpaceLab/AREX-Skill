# Training troubleshooting

Use this matrix to diagnose before retrying a long cache or training action.
Keep the first recovery step read-only and run
`scripts/inspect_training_config.py` with the intended split and overrides.

## Install and import

- **`ModuleNotFoundError` for `navsim`, `nuplan`, Lightning, Torch, or
  torchvision**: check the active Python is the one containing NAVSIM v2 and
  the documented `navsim==2.0.0` dependency set. The verified inspection set
  used Python 3.9, `nuplan-devkit==1.2.0`, `torch==2.0.1+cu117`, and
  `pytorch-lightning==2.2.1`; do not silently mix incompatible Torch and
  torchvision builds.
- **Import works but a builder fails on `cv2`, PIL, map, or geometry symbols**:
  distinguish the EgoStatusMLP CPU path from the TransFuser path. TransFuser
  preprocessing needs its image/LiDAR/geometry optional dependencies even
  though the route can be documented without sensor data.
- **CUDA wheel mismatch**: verify `torch.cuda.is_available()` and the
  Torch/torchvision pair before choosing `gpu` or `16-mixed`. A CPU import is
  enough for a config check but not for a GPU capability claim.

## Optional dependencies and backend

- **`CUDA is not available` or accelerator initialization fails**: use the CPU
  smoke plan in [configuration.md](configuration.md), with `strategy=auto`,
  `precision=32-true`, one batch, and no loader workers. Do not use that result
  to claim TransFuser training parity.
- **Out-of-memory or worker-host-memory pressure**: reduce batch size,
  `dataloader.params.num_workers`, and prefetching; disable pinned memory for a
  CPU plan. TransFuser holds image and LiDAR tensors and can exhaust host RAM
  before GPU memory is reported.
- **DDP hangs or unexpectedly starts many processes**: explicitly set
  `trainer.params.strategy=auto` and `trainer.params.devices=1` for a one-GPU
  check. Reserve `ddp` for a reviewed multi-device plan.
- **Callback/logger errors**: TransFuser's training callback accesses train and
  validation batches and writes images through the trainer logger. For a tiny
  diagnostic plan, either provide a compatible logger/batch or disable the
  callback in a custom agent; do not misdiagnose a visualization callback
  failure as a builder/cache failure.

## Data and config validation

- **`FileNotFoundError` for logs/sensors or empty `SceneLoader`**: resolve
  `OPENSCENE_DATA_ROOT`, `NAVSIM_EXP_ROOT`, and the selected
  `train_test_split.data_split`. Check that the selected log annotations and
  sensor roots exist. `navtrain` uses `trainval` data but a filtered scene list;
  it is not the same as full `trainval`.
- **Synthetic/two-stage inputs are missing**: two-stage test/challenge splits
  can require synthetic sensor and scene roots. They are forbidden for training
  anyway; route the request to evaluation/submission rather than trying to make
  them legal by changing only `data_split`.
- **No samples in cache-only mode**: confirm the cache root exists, the
  `train_logs`/`val_logs` names match cache log directory names exactly, and
  every required builder stem exists under each token. Cache-only mode ignores
  the scene filter, so changing `scene_filter` will not repair this.
- **Cache has files but wrong tensor keys/shapes**: inspect a gzip-pickle with a
  tiny read-only fixture or isolated diagnostic. Confirm the agent setting
  (especially TransFuser `latent`), trajectory sampling, builder implementation,
  and split all match the cache producer. Regenerate into a new root rather than
  overwriting a trusted cache until the mismatch is understood.
- **Data leakage concern**: use disjoint and explicitly recorded train/val log
  lists. The dataset wrapper indexes by tokens while cache-only selection uses
  log folders; a reused cache root can hide an accidental split mix.

## CLI and API misuse

- **Hydra says a required value is missing**: provide
  `experiment_name=...`; the shared output configuration derives `output_dir`
  from it. Use `train_test_split=navtrain` to select the config group, not
  `split=navtrain`.
- **Override appears ignored**: use the exact dotted keys, e.g.
  `trainer.params.max_epochs=1`, `dataloader.params.batch_size=4`,
  `agent=transfuser_agent`, and `agent.config.latent=true`. Inspect the
  composed config rather than assuming a shell variable was interpolated.
- **`TypeError` in DataLoader with `num_workers=0`**: set
  `dataloader.params.prefetch_factor=null` or remove that key for the CPU
  fixture. Prefetching is intended for worker processes.
- **Agent `forward`/loss failure**: feature dictionaries are batched by the
  DataLoader and model outputs must include `trajectory` with `[B,T,3]`.
  Targets come from the `Scene`, features from `AgentInput`; do not call target
  builders with an input-only object.
- **Checkpoint load failure**: pass a real `agent.checkpoint_path` only for a
  compatible learned agent. The loader expects a Lightning `state_dict` and
  strips `agent.`; `null`, a raw incompatible state dict, or a different model
  configuration will fail.

## Workflow-specific failures

- **Contradictory cache flags**: `use_cache_without_dataset=true` with
  `force_cache_computation=true` is invalid by assertion in the training
  runner. Set force computation false and prepare all cache files, or set
  cache-only false and let the SceneLoader-backed Dataset compute/consume data.
  Never rely on an assertion being optimized away.
- **`cache_path` missing in cache-only mode**: the runner requires a non-null
  path, and `CacheOnlyDataset` additionally requires that directory to exist.
  Create/verify it in an approved data-preparation phase; the inspector does
  not create it.
- **Missing only one builder file**: the token is discarded from the valid
  cache set. Compare `get_unique_name()` output, not Python class names, and
  check both feature and target stems.
- **Cache refresh unexpectedly rewrites everything**: `force_cache_computation`
  deliberately uses every `SceneLoader` token. Use false for incremental
  missing-only computation and reserve true for an explicitly approved full
  rebuild into an isolated root.
- **Forbidden challenge split selected for training**: stop. `test`, `navtest`,
  two-stage test filters, warmup, and private challenge configurations are not
  legal training sources under the documented challenge rules. Switch to
  `navtrain`, `trainval`, or a deliberate mini split and record the choice.
- **Training starts with an empty validation set**: inspect the resolved
  `val_logs`; the default log-list file is large and a custom filtered split may
  contain no overlap with the selected list. Fix the explicit validation log
  list or scene filter before spending compute.
- **Training is slow while caching**: the SceneLoader-backed `Dataset` can
  compute feature/target caches during construction. For a full dataset, stop
  and plan the separate dataset-caching workflow with bounded workers and disk
  monitoring rather than waiting for a hidden precomputation phase.

## Synthetic difficult cases

1. **Contradictory flags**: a composed config has
   `use_cache_without_dataset: true`, `force_cache_computation: true`, and a
   non-null cache path. The safe result is a preflight error naming the runner
   assertion; no SceneLoader, cache writer, or trainer is started.
2. **Forbidden split**: a config requests
   `train_test_split=private_test_hard_two_stage` (or `navhard_two_stage`) with
   `use_cache_without_dataset=false`. The safe result is a training-legality
   error even if paths exist; do not reinterpret a test `data_split` as legal
   training data.
