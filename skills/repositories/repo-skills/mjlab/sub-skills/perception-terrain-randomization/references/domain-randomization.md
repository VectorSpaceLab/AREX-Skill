# Domain Randomization

mjlab domain randomization is usually an `EventTermCfg` that calls a function
from `mjlab.envs.mdp.dr`. These functions write per-environment values into the
MuJoCo Warp model or entity state and declare the model fields they need so mjlab
can expand shared model arrays and recompute derived constants safely.

Use the bundled [`inspect_sensor_terrain.py`](../scripts/inspect_sensor_terrain.py)
helper to list the exact installed signatures for DR functions before writing
version-sensitive code.

## Event placement

| `EventTermCfg.mode` | Fires | Use for |
| --- | --- | --- |
| `"startup"` | Once at environment initialization. | Per-env constants that stay fixed for a run, such as body mass variation. |
| `"reset"` | On episode reset for selected envs. | Episode-to-episode variation: friction, camera pose/FOV, terrain reassignment, initial state. |
| `"interval"` | Periodically during simulation; requires `interval_range_s`. | Cheap perturbations like pushes or low-cost friction changes. |
| `"step"` | Every environment step. | Stateful terms that manage their own timers, such as transient body impulses. |

Prefer `startup` or `reset` for fields that trigger `set_const_0` or `set_const`
recomputation. Frequent interval/step recomputation can dominate runtime.

```python
from mjlab.envs.mdp import dr
from mjlab.managers import EventTermCfg, SceneEntityCfg

foot_friction = EventTermCfg(
    mode="reset",
    func=dr.geom_friction,
    params={
        "asset_cfg": SceneEntityCfg("robot", geom_names=(r".*_foot.*",)),
        "ranges": (0.3, 1.2),
        "operation": "abs",
        "shared_random": True,
    },
)
```

## Sampling grammar

Most field functions share this shape:

```python
dr.some_field(
    env,
    env_ids,
    ranges,
    asset_cfg=SceneEntityCfg("robot", ...),
    distribution="uniform",
    operation="abs",
    axes=None,
    shared_random=False,
)
```

- `env_ids=None` means all environments. Passing a tensor restricts writes to a
  subset.
- `asset_cfg` selects the entity and target names/ids (`geom_names`,
  `body_names`, `joint_names`, `camera_names`, `material_names`, `pair_names`,
  etc.). Name selections accept regex-style patterns when resolved through
  `SceneEntityCfg`.
- `ranges=(low, high)` targets default axes for the field.
- `ranges={axis: (low, high)}` gives per-axis ranges.
- `ranges={"regex": (low, high)}` resolves target names by pattern and applies a
  range per matching group.
- `axes=[...]` overrides which final dimension indices are randomized.
- `shared_random=True` samples one value per environment and shares it across
  all selected entities; environments still differ from one another.

Operations:

| Operation | Meaning | Accumulation behavior |
| --- | --- | --- |
| `"abs"` | Write sampled values directly. | Uses current values, so repeated calls can overwrite with new absolutes. |
| `"scale"` | `default * sampled`. | Uses compile-time defaults to avoid accumulation. |
| `"add"` | `default + sampled`. | Uses compile-time defaults to avoid accumulation. |

Distributions: `"uniform"`, `"log_uniform"`, and `"gaussian"`. Custom
`Operation` and `Distribution` instances may be passed when the same interfaces
are implemented.

Quaternion functions (`geom_quat`, `body_quat`, `site_quat`, `cam_quat`) use
`roll_range`, `pitch_range`, and `yaw_range` in radians, compose perturbations
with defaults, and return unit quaternions without accumulating repeated calls.

## Function families

Exact signatures belong to the installed package and can be inspected with the
bundled script. Use this table for choosing the correct family.

| Family | Functions | Notes |
| --- | --- | --- |
| Geom | `geom_friction`, `geom_pos`, `geom_quat`, `geom_rgba`, `geom_size`, `geom_matid` | Friction defaults to tangential axis 0. `geom_rgba` affects rendering only when no material overrides it. `geom_size` handles primitive bounds. |
| Body | `body_mass`, `body_com_offset`/`body_ipos`, `body_pos`, `body_quat`, `pseudo_inertia` | Mass and COM need full recompute; pseudo-inertia keeps mass/inertia physically valid. |
| Joint/DOF | `joint_damping`/`dof_damping`, `joint_armature`/`dof_armature`, `joint_friction`/`dof_frictionloss`, `joint_stiffness`/`jnt_stiffness`, `joint_limits`/`jnt_range`, `joint_default_pos`/`qpos0`, `encoder_bias` | Alias pairs target the same underlying fields. `encoder_bias` writes entity sensor state, not the model. |
| Site | `site_pos`, `site_quat` | Useful for sensor mount randomization. |
| Camera | `cam_fovy`, `cam_pos`, `cam_quat`, `cam_intrinsic` | `cam_fovy` affects FOV-mode cameras only; use `cam_intrinsic` for intrinsic-parameterized cameras. |
| Light | `light_pos`, `light_dir`, `light_diffuse`, `light_specular`, `light_ambient`, `light_attenuation`, `light_cutoff`, `light_exponent` | Good for visual domain randomization. Cutoff/exponent affect spot lights, not directional lights. |
| Material/texture | `mat_rgba`, `mat_emission`, `mat_specular`, `mat_shininess`, `mat_texrepeat`, `mat_texid` | `mat_texid` samples from `asset_cfg.texture_names`; `mat_texrepeat` should stay positive. |
| Contact pair | `pair_friction` | Requires explicit contact-pair selection; use `isotropic=True` to mirror tangent/rolling axes. |
| Tendon | `tendon_damping`, `tendon_stiffness`, `tendon_friction`/`tendon_frictionloss`, `tendon_armature` | Armature contributes to recomputed constants. |
| Actuator/entity | `pd_gains`, `effort_limits` | Supports built-in/XML/ideal PD-style actuator paths; choose in the MDP components sub-skill. |

Terrain-aware event helpers are not `dr` model-field functions but often live in
the same event dictionary: `randomize_terrain` changes terrain row/column origins
for selected envs, and `reset_root_state_from_flat_patches` places an entity on a
named flat patch when available.

## Field expansion and recompute implications

MuJoCo Warp stores many model arrays once and broadcasts them across all worlds.
Per-environment DR needs real per-world storage. Built-in `dr` functions declare
needed fields with `requires_model_fields`, so the event manager asks the
simulation to expand those fields at startup. Custom DR that writes model arrays
must either use the same decorator or call `sim.expand_model_fields()` before
writing per-env values.

Field expansion allocates GPU memory and invalidates captured CUDA graphs because
array pointers change. mjlab recreates the graph automatically after expansion;
this is a startup cost, not an every-reset cost.

Recompute levels, cheapest to most expensive:

| Level | Typical fields | Meaning |
| --- | --- | --- |
| `none` | `geom_friction`, `geom_rgba`, `dof_damping`, `dof_frictionloss`, `jnt_stiffness`, `jnt_range`, most material/light/camera fields | No derived constants need updating. |
| `set_const_fixed` | Custom gravity-compensation style fields | Recompute body subtree mass terms. Built-in DR rarely exposes this directly. |
| `set_const_0` | `dof_armature`, `tendon_armature`, `body_pos`, `body_quat`, `qpos0`, camera/light references | Recompute inverse weights, tendon length/invweight, actuator acceleration constants, and references. |
| `set_const` | `body_mass`, `body_ipos`/COM, `pseudo_inertia` | Full recomputation; most expensive. |

`geom_size` is a special safe case: it expands `geom_size`, `geom_rbound`, and
`geom_aabb`, then recomputes primitive geom bounds inline. It supports spheres,
capsules, ellipsoids, cylinders, and boxes. Do not use it on planes,
heightfields, meshes, or SDF geoms.

Camera FOV/intrinsic field expansion recreates the sensor context and disables
precomputed render rays, because the pixel-to-ray mapping becomes per-world.
Account for the extra render cost in camera-heavy environments.

## High-value recipes

### Randomize camera extrinsics and intrinsics

```python
camera_pose = EventTermCfg(
    mode="reset",
    func=dr.cam_pos,
    params={
        "asset_cfg": SceneEntityCfg("robot", camera_names=("wrist_cam",)),
        "ranges": {0: (-0.02, 0.02), 1: (-0.02, 0.02), 2: (-0.01, 0.01)},
        "operation": "add",
    },
)

camera_zoom = EventTermCfg(
    mode="reset",
    func=dr.cam_intrinsic,
    params={
        "asset_cfg": SceneEntityCfg("robot", camera_names=("wrist_cam",)),
        "ranges": {0: (0.9, 1.1), 1: (0.9, 1.1)},
        "operation": "scale",
        "shared_random": True,
    },
)
```

Use `cam_fovy` instead of `cam_intrinsic` only when the camera is FOV-based.

### Randomize terrain or foot contact friction

```python
terrain_friction = EventTermCfg(
    mode="reset",
    func=dr.geom_friction,
    params={
        "asset_cfg": SceneEntityCfg("terrain", geom_names=("terrain.*",)),
        "ranges": (0.4, 1.1),
        "operation": "abs",
        "axes": [0],
    },
)
```

For explicit MuJoCo contact pairs, prefer `pair_friction` with
`isotropic=True` so tangential and rolling axes remain symmetric:

```python
pair_friction = EventTermCfg(
    mode="reset",
    func=dr.pair_friction,
    params={
        "asset_cfg": SceneEntityCfg(
            "robot",
            pair_names=("left_foot_floor", "right_foot_floor"),
        ),
        "ranges": (0.4, 1.0),
        "axes": [0],
        "shared_random": True,
        "isotropic": True,
    },
)
```

### Disturb a robot during the episode

Use `push_by_setting_velocity` for instantaneous, mass-independent velocity
kicks. Use `apply_external_force_torque` for a steady wrench that persists until
overwritten or cleared. Use class-based `apply_body_impulse` with `mode="step"`
for transient random bumps that manage duration, cooldown, and clearing.

## Visualization expectations

The native viewer syncs per-world model fields before rendering, so it can show
most geom, material, inertia, camera, and light changes. Viser reads many dynamic
poses directly from GPU data, but some baked mesh appearance changes such as
`geom_rgba`, `geom_size`, and `mat_texid` may not update visually even though the
simulation fields changed. Use numeric checks or camera-render checks when visual
appearance is the verification target.

## Verification ladder

- Config-only verification can inspect function signatures, build event configs,
  and confirm field/preset names without CUDA.
- Per-world model-field verification needs a real mjlab environment, expanded
  fields, a targeted reset/startup/interval event, and assertions that only the
  selected environments/entities/axes changed.
- Camera/raycast DR claims need a sensor context and `sim.sense()` after the DR
  event; CPU config success is not proof that rendered images or ray hits update.
