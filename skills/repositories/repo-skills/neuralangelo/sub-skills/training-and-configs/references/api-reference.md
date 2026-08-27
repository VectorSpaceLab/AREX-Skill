# Training API reference

This reference summarizes the Neuralangelo training stack at an operational
level. It is for agents configuring and launching training, not for reimplementing
the model.

## Entry point: `train.py`

`train.py` performs this sequence:

1. Parse known launch flags and collect unknown args as config overrides.
2. Load `Config(args.config)`.
3. Parse override arguments with `parse_cmdline_arguments`.
4. Apply `recursive_update_strict`, which rejects unknown override paths.
5. Initialize distributed training unless `--single_gpu` is present.
6. Seed random generators by rank.
7. Initialize the logdir and save the final merged config.
8. Initialize cuDNN settings from `cfg.cudnn`.
9. Build `Trainer` through `get_trainer(cfg, is_inference=False, seed=args.seed)`.
10. Attach train and val data loaders.
11. Load checkpoint state through `trainer.checkpointer.load(...)`.
12. Initialize W&B in online or disabled mode.
13. Enter `trainer.train(...)` and finalize W&B at the end.

Launch flags are described in `references/workflows.md`.

## Config API

### `imaginaire.config.Config`

- Subclasses an attribute dictionary, so nested YAML keys are available as
  `cfg.model.render.rand_rays` as well as dictionary keys.
- Loads base defaults, then the requested YAML file and its `_parent_` chain.
- Recursively merges mappings. Lists replace the inherited value; they are not
  concatenated.
- Saves the final config to `<logdir>/config.yaml` via `save_config`.

### `parse_cmdline_arguments`

Supported override forms:

- `--key1.key2=value` → YAML-parsed value
- `--key1.key2=` → null
- `--key1.key2` → true
- `--key1.key2!` → false

### `recursive_update_strict`

Every override key must already exist in the inherited config. This protects
against typos but means new experimental keys must be added to YAML first before
being overridden at the command line.

## Trainer construction

`imaginaire.trainers.utils.get_trainer.get_trainer(cfg, is_inference, seed)`
imports the module named by `cfg.trainer.type` and constructs its `Trainer`.
For Neuralangelo this is `projects.neuralangelo.trainer.Trainer`.

The base trainer:

- Sets the active CUDA device from `cfg.local_rank`.
- Builds the model from `cfg.model.type` and moves it to CUDA.
- Builds optimizer and scheduler when not in inference mode.
- Wraps the model in DDP when distributed is initialized, otherwise a simple
  wrapper.
- Initializes AMP scaler, losses, checkpointer, timer, logging attributes, and
  val parameters.
- Builds data loaders through the configured data module.

## Neuralangelo `Trainer`

`projects.neuralangelo.trainer.Trainer` extends the NeRF base trainer and owns
training losses and Neuralangelo-specific progression:

- Losses:
  - `render`: L1 RGB loss, weighted by `trainer.loss_weight.render`.
  - `eikonal`: SDF gradient regularization when configured.
  - `curvature`: numerical curvature regularization when configured.
- Metrics:
  - PSNR for train and val.
  - SDF variance parameter, curvature weight, eikonal weight, normal epsilon,
    and active hash-grid levels are logged to W&B.
- Coarse-to-fine:
  - When hash-grid coarse-to-fine is enabled, active levels and normal epsilon
    are updated at the start of each iteration.
  - Curvature loss weight is warmed up and later decayed according to active
    hash-grid resolution.
- Validation:
  - `validation_iter` triggers full-image validation through the val data loader.
  - W&B image logging includes target/render/error RGB, normal, inverse depth,
    and opacity maps.

## Neuralangelo `Model`

`projects.neuralangelo.model.Model(cfg_model, cfg_data)` builds the surface and
background renderers used by the trainer.

Main components:

- `NeuralSDF`: SDF MLP plus positional or tiny-cuda-nn hash-grid encoding.
- `NeuralRGB`: RGB head that can use points, normals, view direction encoding,
  SDF features, and optional appearance embeddings.
- `BackgroundNeRF`: optional background branch using Fourier encoding and view
  encoding.
- `s_var`: learnable SDF variance parameter initialized by
  `model.object.s_var.init_val`.
- `ray_generator`: samples random rays for train and full image rays for val.

Forward behavior:

- `forward(data)` renders sampled training rays using `data["pose"]`,
  `data["intr"]`, `data["idx"]`, and `data["ray_idx"]`.
- `inference(data)` renders full validation images and returns `rgb_map`,
  `opacity_map`, `depth_map`, and `normal_map`.
- Appearance embeddings require `cfg_data.num_images` and use the sample index
  to look up per-image codes.

Operational consequences:

- `tinycudann` is required when `model.object.sdf.encoding.type: hashgrid`.
- `model.render.rand_rays`, sample counts, hash-grid `dict_size`, and hash-grid
  `dim` dominate train memory.
- Validation memory is affected by `data.val.image_size`, `data.val.batch_size`,
  and `data.val.subset`.

## Neuralangelo `Dataset`

`projects.neuralangelo.data.Dataset(cfg, is_inference=False)` reads prepared
Instant-NGP-style JSON data.

Expected inputs:

- `cfg.data.root/transforms.json`
- Images referenced by each frame's `file_path`
- JSON camera fields `fl_x`, `fl_y`, `sk_x`, `sk_y`, `cx`, `cy`
- `sphere_center` and `sphere_radius`
- `frames[*].transform_matrix`

Train samples include:

- `idx`: image index
- `ray_idx`: random ray indices
- `image_sampled`: RGB samples in `[0, 1]`
- `intr`: resized camera intrinsics
- `pose`: world-to-camera pose

Validation samples include full images plus `intr` and `pose`.

Dataset settings:

- `data.preload: true` loads images and cameras up front with worker threads.
- `data.train.subset` and `data.val.subset` select evenly spaced subsets when
  set.
- `data.readjust.center` and `data.readjust.scale` refine the normalized scene
  sphere without regenerating JSON.

Raw COLMAP reading and JSON generation use helper modules under the repository's
COLMAP utilities, but that is a data-preparation responsibility. During
training, only the generated JSON and images are consumed.

## Optimizer and scheduler

The base config uses:

```yaml
optim:
  type: AdamW
  params:
    lr: 1e-3
    weight_decay: 1e-2
  sched:
    iteration_mode: true
    type: two_steps_with_warmup
    warm_up_end: 5000
    two_steps: [300000, 400000]
    gamma: 10.0
```

Neuralangelo's scheduler returns a warmup factor until `warm_up_end`, then full
learning rate, then one or two `gamma` decays after the configured steps.

## Checkpointer

The checkpointer saves model, optimizer, scheduler, epoch, and iteration. It
writes into `cfg.logdir` and maintains `latest_checkpoint.txt` as a pointer to
the most recent named checkpoint. When `--resume` is true:

- If `--checkpoint` is absent, it attempts to read `latest_checkpoint.txt` from
  the logdir.
- It restores epoch and iteration.
- It restores optimizer and scheduler when requested by the caller; `train.py`
  requests both.
- Scheduler `last_epoch` is set from resumed iteration when the schedule is in
  iteration mode.

`checkpoint.strict_resume` controls strict model-state loading. Default base
behavior is strict.

## W&B behavior

`train.py` calls `trainer.init_wandb` with:

- `project=args.wandb_name`
- `mode="disabled"` when `--debug` or no `--wandb`, otherwise `online`
- `resume=args.resume`
- `use_group=True`

The trainer writes or reuses `wandb_id.txt` in the logdir. In group mode, the
last two logdir components become W&B group and run name. Only the master
process initializes and logs W&B entries.

## Safe CLI/script boundaries

The training sub-skill may help users call:

- `train.py`
- `projects/neuralangelo/scripts/generate_config.py` only for understanding
  generated custom config fields or rerouting to data preparation

It must reroute these tasks away from training:

- `convert_data_to_json.py`, `convert_dtu_to_json.py`, `convert_tnt_to_json.py`,
  COLMAP wrappers, FFmpeg wrappers, pose notebooks: `data-preparation`
- `extract_mesh.py`: `mesh-extraction`

Safe help checks for `train.py`, data conversion scripts, `generate_config.py`,
and `extract_mesh.py` were verified during environment preparation, but runtime
training still requires the user's active CUDA-capable environment.
