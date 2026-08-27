# Configuration guide

Neuralangelo training is controlled by YAML files plus strict command-line
overrides. The active config is merged, printed, and saved to the logdir as
`config.yaml` before training begins.

## Config loading and inheritance

The training entry point creates `Config(args.config)` and then applies any
unknown command-line `--key=value` arguments as config overrides.

Load order:

1. Imaginaire base defaults are loaded first.
2. The requested YAML file is loaded.
3. If that YAML contains `_parent_`, the parent is loaded and then the child
   recursively overrides the parent.
4. Command-line overrides are parsed as YAML values and applied with strict key
   checking.

Common parent chain examples:

```yaml
# custom, DTU, and Tanks and Temples configs inherit the Neuralangelo base.
_parent_: projects/neuralangelo/configs/base.yaml
```

Practical implications:

- A child YAML only needs fields that differ from the parent.
- Command-line override keys must already exist after inheritance. A typo such
  as `--optim.param.lr=...` raises a key error because `optim.param` does not
  exist.
- Override values are YAML-parsed: `1e-3` becomes a number, `[300,400]` becomes
  a list, `false` becomes Boolean false, and an empty assignment becomes null.
- Overrides without `=` become true; overrides ending with `!` become false.

Examples:

```bash
# Change a scalar.
--optim.params.lr=5e-4

# Change a nested list.
--data.val.image_size=[200,300]

# Set a nullable field to null.
--data.train.subset=

# Toggle a Boolean false using the parser shorthand.
--model.background.enabled!
```

Use `scripts/inspect_config_summary.py --override key=value` before a launch to
verify that override paths exist.

## Built-in config families

### `projects/neuralangelo/configs/base.yaml`

The base config defines the default training schedule, logging cadence,
checkpoint cadence, trainer/model/data modules, Neuralangelo model structure,
optimizer, scheduler, and default synthetic data path.

Important defaults:

- `max_iter: 500000`
- `checkpoint.save_iter: 20000`
- `validation_iter: 5000`
- `wandb_scalar_iter: 100`
- `wandb_image_iter: 10000`
- `trainer.type: projects.neuralangelo.trainer`
- `model.type: projects.neuralangelo.model`
- `optim.type: AdamW`
- `optim.params.lr: 1e-3`
- `optim.sched.type: two_steps_with_warmup`
- `optim.sched.warm_up_end: 5000`
- `optim.sched.two_steps: [300000, 400000]`

Default model highlights:

- SDF hash-grid encoding with `levels: 16`, `dict_size: 22`, `dim: 8`, and
  hash-grid range `[-2, 2]`.
- Coarse-to-fine hash-grid activation enabled with `init_active_level: 4` and
  `step: 5000`.
- Numerical SDF gradients with `taps: 4`.
- Background NeRF enabled.
- Random training rays: `model.render.rand_rays: 512`.
- Object samples: `coarse: 64`, `fine: 16`, `num_sample_hierarchy: 4`.
- Background samples: `32`.
- Appearance embeddings disabled by default.

### `projects/neuralangelo/configs/dtu.yaml`

DTU inherits the base config and switches to Neuralangelo's JSON/image dataset:

- `data.type: projects.neuralangelo.data`
- Example root: `datasets/dtu/dtu_scan24`
- Train image size `[1200, 1600]`, batch size `1`
- Validation image size `[300, 400]`, batch size `1`, subset `1`
- Appearance embeddings disabled
- SDF `s_var.init_val: 1.4`

Use DTU as a template for calibrated static objects when lighting is stable and
per-image appearance modeling is not needed.

### `projects/neuralangelo/configs/tnt.yaml`

Tanks and Temples inherits the base config and uses the Neuralangelo dataset:

- Example root: `datasets/tanks_and_temples/Barn`
- `data.num_images: 410`
- Train image size `[835, 1500]`, batch size `1`
- Validation image size `[300, 540]`, batch size `1`, subset `1`
- Appearance embeddings enabled with dimension `8`
- Coarse-to-fine starts at active level `8`

Use this as a template for larger scenes and appearance variation. If the scene
requires `appear_embed.enabled: true`, set `data.num_images` to the training
image count.

### `projects/neuralangelo/configs/custom/<scene>.yaml`

Generated custom configs inherit the base config and usually set:

- `data.type: projects.neuralangelo.data`
- `data.root` to the prepared data directory
- `data.train.image_size` from the image resolution
- `data.val.image_size` from a short-side target
- `data.readjust.center` and `data.readjust.scale`
- Scene-type-specific geometry settings:
  - `object`: outside-in false, coarse-to-fine initial level `4`
  - `outdoor`: outside-in false, coarse-to-fine initial level `8`
  - `indoor`: inside-out true, background disabled, background samples `0`

Custom config generation, COLMAP, and bounding sphere adjustment belong to
`data-preparation`; this sub-skill only validates and uses the resulting YAML.

## Required data-related fields

The Neuralangelo dataset class expects:

```yaml
data:
  type: projects.neuralangelo.data
  root: <prepared-data-root>
  preload: true
  num_workers: 4
  num_images: <required when appearance embeddings are enabled>
  train:
    image_size: [H, W]
    batch_size: 1
    subset:
  val:
    image_size: [H, W]
    batch_size: 1
    subset: 1
    max_viz_samples: 16
  readjust:
    center: [0.0, 0.0, 0.0]
    scale: 1.0
```

`data.root/transforms.json` must provide camera intrinsics, `sphere_center`,
`sphere_radius`, and a `frames` list whose `file_path` values point to images
under `data.root`.

`data.readjust.center` is added to the JSON sphere center before normalization;
`data.readjust.scale` multiplies the JSON sphere radius. Bad values here can crop
or overscale the reconstruction volume.

## Model and trainer knobs that agents should know

| Config path | Meaning | Operational advice |
| --- | --- | --- |
| `model.object.sdf.encoding.hashgrid.dict_size` | Hash table log2 size for tiny-cuda-nn hash grid | Primary VRAM knob; lower for smaller GPUs. |
| `model.object.sdf.encoding.hashgrid.dim` | Features per hash-grid level | Primary VRAM/quality knob. |
| `model.object.sdf.encoding.coarse2fine.init_active_level` | Initial active hash-grid levels | Smaller for object-centric scenes, larger for broader scenes. |
| `model.object.sdf.mlp.inside_out` | SDF sign convention | Indoor rooms may use true; objects/outdoor usually false. |
| `model.background.enabled` | Background NeRF branch | Disable for indoor room-style configs if no outside background is desired. |
| `model.render.rand_rays` | Random rays per image per training sample | Lower to reduce per-step memory. |
| `model.render.num_samples.*` | Coarse/fine/background samples per ray | Lower to reduce memory and time; quality may drop. |
| `model.appear_embed.enabled` | Per-image appearance embeddings | Requires `data.num_images`; useful for varying exposure/white balance. |
| `trainer.loss_weight.render/eikonal/curvature` | Loss weights | Defaults are tuned for Neuralangelo; change one at a time. |
| `trainer.amp_config.enabled` | Automatic mixed precision | Defaults false; enable only after a smoke run proves numerical stability. |
| `trainer.grad_accum_iter` | Gradient accumulation | Can trade speed for effective batch size; checkpoint/resume preserves optimizer state. |
| `optim.sched.*` | Learning-rate schedule | Default is warmup then two step decays at 300k/400k iterations. |

## Memory reduction recipes

The default configuration is designed for large CUDA GPUs. The repository notes
that default Neuralangelo training expects roughly 24 GB of GPU memory. If the
user has less VRAM, start with the hash-grid knobs:

| Approximate VRAM | Suggested overrides |
| --- | --- |
| 8 GB | `--model.object.sdf.encoding.hashgrid.dict_size=20 --model.object.sdf.encoding.hashgrid.dim=4` |
| 12 GB | `--model.object.sdf.encoding.hashgrid.dict_size=21 --model.object.sdf.encoding.hashgrid.dim=4` |
| 16 GB | `--model.object.sdf.encoding.hashgrid.dict_size=21 --model.object.sdf.encoding.hashgrid.dim=8` |

Additional reductions, in order of lowest surprise:

```bash
--model.render.rand_rays=256
--data.train.batch_size=1
--data.val.batch_size=1
--data.val.image_size=[200,300]
--data.val.subset=1
--data.val.max_viz_samples=4
--wandb_image_iter=20000
--validation_iter=10000
```

Stronger changes that may affect quality or behavior:

```bash
--model.render.num_samples.coarse=48
--model.render.num_samples.fine=8
--model.render.num_sample_hierarchy=3
--model.render.num_samples.background=16
--model.background.enabled=false
```

If evaluation OOM happens but training is stable, reduce only `data.val.*`,
`validation_iter`, and `wandb_image_iter` first.

## Validation checklist

Before launch, verify:

- `--config` file exists and parent files resolve from the project root.
- `data.type` matches the dataset format. For prepared custom/DTU/TNT data, this
  should be `projects.neuralangelo.data`.
- `data.root` exists and contains `transforms.json` plus the referenced images.
- `data.train.image_size` and `data.val.image_size` are `[height, width]`, not
  `[width, height]`.
- If appearance embeddings are enabled, `data.num_images` is not null and equals
  the number of training frames, not the validation subset size.
- For multi-GPU training, the number of visible CUDA devices equals
  `torchrun --nproc_per_node`.
- `tinycudann` imports in the active environment and was built for the installed
  CUDA/PyTorch combination.
- `--logdir` is a new directory for a new run, or the original directory for a
  `--resume` run.
- For resume, prefer `--config=logs/<group>/<name>/config.yaml` to preserve the
  exact merged config used by the original run.
