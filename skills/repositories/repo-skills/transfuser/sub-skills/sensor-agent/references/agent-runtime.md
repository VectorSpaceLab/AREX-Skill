# Agent Runtime And Checkpoint Contract

## Runtime Readiness Boundary

The learned agent is implemented for the CARLA Leaderboard sensor track. Its
model-side imports were observed working in an isolated Python 3.7 CUDA
environment with:

- PyTorch 1.12.1+cu113
- `mmcv-full` 1.6.0
- `mmdet` 2.25.0
- `timm` 0.6.7

The config, data, model, and train modules imported successfully. This is not
proof of an evaluation run: the CARLA Python module was absent. A real agent
run still requires the external CARLA **0.9.10.1** Python API and server,
together with compatible Leaderboard and scenario-runner code. The bundled
validator intentionally does not fill this gap.

## Leaderboard Interface

The agent module's discovery hook is:

```python
def get_entry_point():
    return "HybridAgent"
```

The returned name identifies a class derived from the Leaderboard
`AutonomousAgent` base. The relevant interface contract is:

- construction receives `path_to_conf_file`; the base calls `setup(path)`;
- `setup` selects `Track.SENSORS` and initializes runtime state;
- `sensors()` returns sensor specification dictionaries with unique IDs;
- `run_step(input_data, timestamp)` returns `carla.VehicleControl`;
- the base agent call obtains synchronized data from `SensorInterface`, obtains
  simulator time, calls `run_step`, and forces `manual_gear_shift = False`;
- `set_global_plan(global_plan_gps, global_plan_world_coord)` provides the route
  before the learned agent initializes its route planner. The bundled
  Leaderboard base downsamples the world-coordinate plan and stores the GPS
  plan in `_global_plan`.

`HybridAgent.destroy()` drops the model ensemble. Treat teardown as mandatory
in evaluator code that can instantiate more than one agent.

## `TEAM_CONFIG` Directory Schema

Pass a directory as `TEAM_CONFIG`. It must contain:

```text
team-config/
  args.txt
  model_40.pth       # one or more .pth files
  model_45.pth       # optional: adds another ensemble member
```

`args.txt` is JSON, despite its `.txt` suffix. Every regular file ending in
`.pth` is treated as a model and loaded into the ensemble; optimizer
checkpoints must therefore not be copied into this directory with a `.pth`
suffix. A directory with zero `.pth` files creates an empty ensemble and cannot
produce controls.

Training writes `args.txt` from the parsed training arguments. Runtime consumes
the following architecture-critical keys when present:

| Key | Accepted form | Runtime default when absent | Effect |
| --- | --- | --- | --- |
| `backbone` | string | `transFuser` | One of `transFuser`, `late_fusion`, `geometric_fusion`, `latentTF` |
| `image_architecture` | non-empty string | `resnet34` | Image encoder architecture |
| `lidar_architecture` | non-empty string | `resnet18` | LiDAR encoder architecture; still part of model construction |
| `use_velocity` | JSON boolean or 0/1 | `true` | Includes ego-speed conditioning according to the trained architecture |
| `sync_batch_norm` | JSON boolean or 0/1 | config default `false` | Converts model batch normalization before loading |
| `use_point_pillars` | JSON boolean or 0/1 | config default `false` | Uses raw-cloud point pillars instead of histogram voxelization |
| `n_layer` | positive integer | config default `8` | Transformer depth |
| `use_target_point_image` | JSON boolean or 0/1 | config default `false` | Concatenates a target-point raster with the LiDAR-like input |

Do not rely on runtime defaults for a trained checkpoint. The training CLI's
observed defaults differ for several fields: image and LiDAR architectures are
`regnety_032`, `use_velocity` is `0`, `n_layer` is `4`, and
target-point-image use is `1`. Preserve the `args.txt` produced with the model.
A valid JSON file with the wrong architecture can still instantiate a model
whose parameters do not match the weights.

The training help states that velocity input is intended for the `transFuser`
backbone. Treat `use_velocity=true` with another backbone as a provenance check,
not as a harmless generic toggle.

## Backbones And Sensor Consequences

- `transFuser`: image and LiDAR fusion; requires the physical `lidar` sensor.
- `late_fusion`: image and LiDAR late fusion; requires `lidar`.
- `geometric_fusion`: image/LiDAR fusion with explicit BEV-camera
  correspondences; requires raw `lidar` as well as its prepared BEV form.
- `latentTF`: image-only runtime path. `sensors()` omits physical LiDAR and
  `run_step` supplies a zero tensor of shape `[1, 2, 256, 256]` as a placeholder.

`latentTF` is the sole built-in LiDAR-omission case. Do not remove LiDAR for any
other backbone. Conversely, do not diagnose the absent LiDAR sensor as an error
when the selected backbone is exactly `latentTF`.

## Checkpoint Loading And CUDA Placement

For each `.pth` file the implementation:

1. constructs `LidarCenterNet(config, "cuda", backbone, image_architecture,
   lidar_architecture, use_velocity)`;
2. optionally converts it with `torch.nn.SyncBatchNorm.convert_sync_batchnorm`;
3. loads the checkpoint with a `cuda:0` map location;
4. rewrites every key by removing its first seven characters;
5. calls `load_state_dict(..., strict=False)`;
6. calls `.cuda()` and `.eval()`.

Image, LiDAR, target-point, target-point-image, velocity, geometric
correspondence, predicted-waypoint, and dummy-latent tensors are also moved to
CUDA. All ensemble members occupy the same CUDA device. There is no implemented
CPU inference fallback and no model sharding across GPUs.

### DDP `.module` Prefix Caveat

The seven-character rewrite is intended to remove the `module.` prefix emitted
when training saves a DistributedDataParallel model's state dict. It is
unconditional in the runtime source. A single-GPU training checkpoint generally
has unprefixed keys; removing seven characters corrupts them. The project README
explicitly warns that this line must be removed for a single-GPU checkpoint.

A safer adaptation is conditional normalization: inspect the state-dict keys,
strip `module.` only when all relevant keys have that prefix, and leave already
unprefixed keys unchanged. Never mix prefix styles silently. Because loading is
`strict=False`, a bad rewrite may not stop immediately; require a high key-match
coverage and investigate missing/unexpected keys before evaluation.

`sync_batch_norm` must also match training. Conversion is performed before
loading so SyncBatchNorm-trained parameters land on compatible modules.

## Ensemble Semantics

Every `.pth` file becomes one independent network. At each inference step:

- each model predicts waypoints and rotated bounding boxes;
- waypoint tensors are stacked and averaged across models;
- one configured augmentation angle (`0` degrees) is transformed back and then
  median-reduced, which is currently an identity-like reduction;
- boxes from all models are flattened and class-agnostic polygon IoU NMS keeps
  the highest-confidence box in each overlap group;
- the PID controller is called on `nets[0]`, but it consumes the ensemble-mean
  waypoints. PID state therefore lives in the first network's controller.

Ensembling multiplies GPU memory use. The order from `os.listdir` is not sorted,
so do not make first-network PID state depend on checkpoint filename ordering.
Use architecturally identical checkpoints and the same `args.txt` for all
members.

## Safe Preflight

Run:

```bash
python scripts/validate_agent_config.py /path/to/team-config --json
```

The preflight checks JSON shape, architecture-critical fields, ensemble file
count, file size, and static checkpoint container signatures. It reports the
backbone-dependent expected sensor IDs. It does not deserialize pickle-based
PyTorch checkpoints; only trusted checkpoints should later be loaded by the
actual agent runtime.

Evidence distilled into this reference came from the project evaluation guide,
the learned submission agent, model/config/training modules, and the bundled
Leaderboard autonomous-agent interface at source revision `9d413b2` on branch
`2022`.
