# Training configuration and resources

## Hydra composition

The training entry point composes `default_training` with shared common and
evaluation settings, a train/validation log list, and an `agent` config group.
The important resolved paths are:

- `navsim_log_path`: derived from `OPENSCENE_DATA_ROOT`, `navsim_logs`, and
  `train_test_split.data_split`;
- `original_sensor_path`: derived from `OPENSCENE_DATA_ROOT`, `sensor_blobs`,
  and `train_test_split.data_split`;
- `cache_path`: by default under `NAVSIM_EXP_ROOT/training_cache`;
- `output_dir`: by default under `NAVSIM_EXP_ROOT/<experiment_name>/<timestamp>`.

The selected split's `scene_filter` controls scene extraction when a
`SceneLoader` is built. In cache-only mode the scene filter is ignored and
`train_logs`/`val_logs` select cache log folders instead. Validate the resolved
paths and log lists before approving a run; interpolation strings are not proof
that the directories exist.

## Training split legality

The source documentation distinguishes downloadable OpenScene data splits from
filtered NAVSIM scene splits. For training, use a source whose purpose is
training and document it in the experiment record:

| Use for training planning | Underlying data | Notes |
|---|---|---|
| `navtrain` | `trainval` | Recommended filtered NAVSIM training split |
| `trainval` | `trainval` | Full standard training/validation scenes; much larger |
| `mini` | `mini` | Small demo split for smoke planning |
| `navmini` | `mini` | Filtered mini scenes; use only for a deliberate mini experiment |

Reject these for challenge training: `test`, `navtest`, `navtest_two_stage`,
`navhard_two_stage`, `navsafe_two_stage`, `warmup_two_stage`,
`warmup_navsafe_two_stage_extended`, and `private_test_hard_two_stage` (also
recognize the older shorthand `private_test_two_stage`). The challenge rules
prohibit using test/challenge/private test data for training. A custom config
whose `data_split` resolves to `test` should be treated as test data even if a
custom scene filter has a convenient name.

Do not confuse `navtrain` and `trainval`: both resolve to `data_split=trainval`,
but `navtrain` uses a filtered scene list. Likewise, `navtest` and the two-stage
variants resolve through test data but are not training substitutes.

## Agent configuration

The maintained baseline groups instantiate:

- `ego_status_mlp_agent`: no sensors, one `ego_status_feature` builder, one
  trajectory target, hidden layer size 512, and learning rate `1e-4`;
- `transfuser_agent`: current front/left/right cameras and current LiDAR unless
  `config.latent=true`, plus auxiliary detection/map/trajectory targets,
  learning rate `1e-4`, and a TransFuser callback.

Both baseline trajectory sampling configs are 4 seconds at 0.5-second intervals.
The target is therefore eight `[x, y, heading]` poses. Changing sampling changes
model output dimensions and target cache content; change the cache identity at
the same time.

The training wrapper expects the agent to provide feature builders, target
builders, `forward`, a scalar `compute_loss`, and an optimizer. It uses
`DataLoader(..., shuffle=True)` for training and `shuffle=False` for validation.
Its logging keys are `train/loss` and `val/loss`.

## DataLoader and worker planning

The default loader is batch size 64, four loader workers, pinned memory, and
prefetch factor 2. These are throughput-oriented defaults, not universal
requirements:

- For a CPU/import or tiny-fixture check, use a small batch and
  `dataloader.params.num_workers=0`, `pin_memory=false`, and disable or null
  `prefetch_factor` as required by the installed PyTorch version.
- For CUDA, pinned memory and a modest worker count can improve transfer, but
  account for host RAM and image/LiDAR preprocessing. Increase workers only
  after checking file descriptors and cache I/O.
- TransFuser is sensor- and map-heavy; a CPU run can validate imports and
  tensor contracts but is not evidence of useful training throughput.

The shared `worker` config is used by the separate dataset-caching runner. The
training runner itself uses DataLoader workers. For conservative cache planning,
`worker=sequential` is the easiest override. Thread/process/Ray workers should
be bounded explicitly and only used with an approved storage and memory plan.

## Accelerator and precision planning

The shipped trainer defaults are `accelerator=gpu`, `strategy=ddp`,
`precision=16-mixed`, one node, 100 epochs, and full train/validation batches.
On one GPU, plan an override such as:

```text
trainer.params.accelerator=gpu
trainer.params.strategy=auto
trainer.params.devices=1
trainer.params.precision=16-mixed
```

On a host where only a CPU smoke is approved, plan:

```text
trainer.params.accelerator=cpu
trainer.params.strategy=auto
trainer.params.precision=32-true
trainer.params.max_epochs=1
trainer.params.limit_train_batches=1
trainer.params.limit_val_batches=1
dataloader.params.num_workers=0
dataloader.params.pin_memory=false
dataloader.params.prefetch_factor=null
```

Do not claim that CPU settings reproduce CUDA memory, mixed-precision, or
TransFuser performance behavior. Conversely, do not leave `strategy=ddp` in a
single-device plan without checking Lightning's device resolution; an explicit
`strategy=auto`/`devices=1` plan avoids accidental multi-process startup.

## Checkpoints and outputs

A planned run should give `experiment_name` and an approved `output_dir`.
Lightning's checkpointing behavior and callback configuration should be
inspected in the resolved run configuration; do not rely on a guessed filename.
The learned-agent `initialize()` methods load a mapping with a `state_dict` and
strip the `agent.` prefix from keys. For a later evaluation or inference plan,
provide the exact checkpoint through `agent.checkpoint_path=<path>` and keep the
same model configuration and trajectory sampling used to create it. A null or
incompatible path fails at initialization; a checkpoint from a different
builder/config is not made compatible by changing the filename.

## Safe config inspection

Use the bundled `scripts/inspect_training_config.py` to check split legality,
cache flag combinations, required cache-path intent, and the resource plan. It
parses YAML and dotted overrides without importing Hydra or constructing a
SceneLoader. It never creates directories, touches data, downloads files, or
launches training.
