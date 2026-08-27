# Sensors

mjlab sensors are configured on `SceneCfg.sensors`, not inside an individual
`EntityCfg`. A sensor may reference an entity element with `ObjRef(entity=...)`,
but the scene owns the sensor lifecycle and access path. Camera and raycast
sensors also require the scene's shared sensor context, which is prepared during
scene/simulation initialization and populated by `sim.sense()`.

Use the bundled [`inspect_sensor_terrain.py`](../scripts/inspect_sensor_terrain.py)
helper to print the exact installed signatures for the config classes below.

## Sensor selection map

| Need | Prefer | Key config choices | Runtime output |
| --- | --- | --- | --- |
| Native MuJoCo scalar/vector readings | `BuiltinSensorCfg` | `sensor_type`, `obj`, optional `ref`, optional `cutoff` | `torch.Tensor` shaped `[B, dim]` |
| Foot/self/contact events | `ContactSensorCfg` | `primary`, optional `secondary`, `fields`, `reduce`, `num_slots`, `track_air_time`, `history_length` | `ContactData` dataclass |
| Terrain height map or obstacle scan | `RayCastSensorCfg` | `frame`, `pattern`, `ray_alignment`, `max_distance`, `include_geom_groups` | `RayCastData` dataclass |
| Per-foot/per-frame clearance | `TerrainHeightSensorCfg` | Raycast fields plus `reduction` | `TerrainHeightData.heights` |
| RGB, depth, segmentation | `CameraSensorCfg` | `camera_name` or `pos`/`quat`, `data_types`, image size, render settings | `CameraSensorData` dataclass |

`B` means number of parallel environments. `P` means resolved primary contact
elements. `F` means raycast attachment frames. `N` means rays per frame or total
rays where noted.

## Built-in sensors

`BuiltinSensorCfg` wraps MuJoCo native sensors and returns a tensor view over
`sim.data.sensordata`. Attach sensors with `ObjRef(type=..., name=..., entity=...)`.
If `entity` is set, the sensor name is prefixed in the compiled model, and the
runtime access key is usually `"entity/sensor_name"`. Sensors already present in
an entity's XML are auto-discovered and exposed with the same entity prefix, so
avoid defining a duplicate scene sensor with the same prefixed name.

| Built-in group | Sensor types | Object requirement |
| --- | --- | --- |
| Site | `accelerometer`, `velocimeter`, `gyro`, `force`, `torque`, `magnetometer`, `rangefinder` | `obj.type="site"` |
| Joint | `jointpos`, `jointvel`, `jointlimitpos`, `jointlimitvel`, `jointlimitfrc`, `jointactuatorfrc` | `obj.type="joint"` |
| Tendon | `tendonpos`, `tendonvel`, `tendonactuatorfrc` | `obj.type="tendon"` |
| Actuator | `actuatorpos`, `actuatorvel`, `actuatorfrc` | `obj.type="actuator"` |
| Frame | `framepos`, `framequat`, `framexaxis`, `frameyaxis`, `framezaxis`, `framelinvel`, `frameangvel`, `framelinacc`, `frameangacc` | `body`, `xbody`, `geom`, `site`, or `camera`; these are the only built-ins that accept `ref` |
| Subtree/misc | `subtreecom`, `subtreelinvel`, `subtreeangmom`, `e_potential`, `e_kinetic`, `clock` | body for subtree; none for energy/clock |

Use `cutoff > 0` to clamp absolute output values in the MuJoCo sensor definition.

```python
from mjlab.sensor import BuiltinSensorCfg, ObjRef

imu_acc = BuiltinSensorCfg(
    name="imu_acc",
    sensor_type="accelerometer",
    obj=ObjRef(type="site", name="imu_site", entity="robot"),
)

base_up = BuiltinSensorCfg(
    name="base_up",
    sensor_type="framezaxis",
    obj=ObjRef(type="body", name="world"),
    ref=ObjRef(type="site", name="imu_site", entity="robot"),
)
```

## Contact sensors

`ContactSensorCfg` expands a `ContactMatch` into one or more primary elements.
Per-contact fields are laid out primary-major: for primary index `i`, slots live
at `i * num_slots : (i + 1) * num_slots`. Use `sensor.primary_names` to map
columns back to resolved element names.

```python
from mjlab.sensor import ContactMatch, ContactSensorCfg

feet_contact = ContactSensorCfg(
    name="feet_ground_contact",
    primary=ContactMatch(
        mode="geom",
        pattern=r".*_foot.*",
        entity="robot",
        exclude=(r".*visual.*",),
    ),
    secondary=ContactMatch(mode="body", pattern="terrain"),
    fields=("found", "force"),
    reduce="maxforce",
    track_air_time=True,
    history_length=5,
)
```

Important contact options:

| Option | Use it when | Notes |
| --- | --- | --- |
| `mode="geom"` | You care about physical collision geoms such as feet or fingers. | Most precise for robot-ground contact. |
| `mode="body"` | A whole named body is the primary/secondary. | Matches body names. |
| `mode="subtree"` | You want contacts for a body and all descendants. | Useful for self-collision sentinels. |
| `secondary=None` | Any contact with the primary counts. | Good for generic collision flags. |
| `secondary_policy="first"` | A secondary regex may match multiple names and the first is acceptable. | Default. Prefer explicit names when order matters. |
| `secondary_policy="any"` | You want no secondary filter after all. | It drops the secondary filter entirely. |
| `secondary_policy="error"` | Multiple secondary matches should fail loudly. | Use for safety-critical contact checks. |
| `reduce="none"` | You need fast raw slots and can tolerate non-deterministic ordering. | Pair with `num_slots > 1` only when needed. |
| `reduce="mindist"` | Keep deepest contacts. | Good for penetration diagnostics. |
| `reduce="maxforce"` | Keep strongest contacts. | Good default for foot-contact policies. |
| `reduce="netforce"` | Sum contacts into one global wrench per primary. | Ignores `num_slots` beyond one. |
| `track_air_time=True` | Gait rewards need first-contact/first-air or contact timing. | Requires `"found"` in `fields`. |
| `history_length > 0` | Contacts may occur within decimation substeps and disappear by policy-step readout. | Set near the environment decimation when detecting short impacts. |
| `global_frame=True` | Consumers expect force/torque in world coordinates. | Requires `normal` and `tangent` unless using `netforce`. |
| `debug=True` | Pattern expansion is unclear. | Prints each generated MuJoCo contact sensor at spec construction. |

Output fields selected by `fields` include `found`, `force`, `torque`, `dist`,
`pos`, `normal`, and `tangent`. Force/torque are 3-vectors; distance is scalar;
position/normal/tangent are global-frame 3-vectors. Air-time fields are
per-primary `[B, P]`. History fields are `[B, P * num_slots, H, ...]` with index
0 as the most recent substep.

## Raycast and terrain-height sensors

`RayCastSensorCfg` attaches rays to a body, site, or geom. A single `ObjRef`
creates one frame; a tuple creates multiple frames such as per-foot probes.
Raycasting uses the shared sensor context, so a standalone sensor object cannot
produce data until it is part of an initialized scene and `sim.sense()` has run.

```python
from mjlab.sensor import GridPatternCfg, ObjRef, RayCastSensorCfg

terrain_scan = RayCastSensorCfg(
    name="terrain_scan",
    frame=ObjRef(type="body", name="base", entity="robot"),
    pattern=GridPatternCfg(size=(1.6, 1.0), resolution=0.1),
    ray_alignment="yaw",
    max_distance=2.0,
    include_geom_groups=(0, 1),
    debug_vis=True,
)
```

Patterns:

| Pattern | Behavior | Best fit |
| --- | --- | --- |
| `GridPatternCfg` | Parallel rays over a metric grid. Coverage does not grow with height. | Height maps and terrain scans. |
| `PinholeCameraPatternCfg` | Diverging rays from one origin. Can be built from explicit FOV, a MuJoCo camera, or an intrinsic matrix. | Depth-camera-like scans. |
| `RingPatternCfg` | Center plus concentric rings. | Per-foot clearance samples. |

Ray alignment controls direction only; the ray origin always follows the
physical frame position:

- `"base"`: full frame rotation.
- `"yaw"`: yaw follows the frame, pitch/roll are ignored; useful for terrain
  scans mounted to tilting bodies.
- `"world"`: directions are fixed in world coordinates.

`RayCastData` provides `distances [B, F*N]` (`-1` on miss), `hit_pos_w`,
`normals_w`, first-frame `pos_w`/`quat_w`, and all-frame
`frame_pos_w`/`frame_quat_w`. Use `include_geom_groups=None` to include all
MuJoCo geom groups; otherwise values must be in `0..5`. `exclude_parent_body`
prevents self-hits from the attached frame's body.

`TerrainHeightSensorCfg` subclasses raycast and adds `data.heights`. It computes
frame `z - hit_z`, handles misses with `max_distance`, and reduces rays within
each frame using `reduction="min"`, `"max"`, `"mean"`, or `"none"`.

```python
from mjlab.sensor import ObjRef, RingPatternCfg, TerrainHeightSensorCfg

foot_height = TerrainHeightSensorCfg(
    name="foot_height_scan",
    frame=(
        ObjRef(type="site", name="left_foot", entity="robot"),
        ObjRef(type="site", name="right_foot", entity="robot"),
    ),
    pattern=RingPatternCfg.single_ring(radius=0.04, num_samples=4),
    max_distance=1.0,
    include_geom_groups=(0,),
    reduction="min",
)
```

## Camera sensors

`CameraSensorCfg` either wraps an existing MuJoCo camera (`camera_name`) or
creates a new camera at `pos`/`quat` under the world body or `parent_body`.
It renders any combination of `"rgb"`, `"depth"`, and `"segmentation"`.

```python
from mjlab.sensor import CameraSensorCfg

wrist_cam = CameraSensorCfg(
    name="wrist_cam",
    camera_name="robot/wrist_camera",
    width=160,
    height=120,
    data_types=("rgb", "depth", "segmentation"),
    clone_data=True,
)
```

Camera output shapes:

| Field | Shape | Type | Notes |
| --- | --- | --- | --- |
| `rgb` | `[B, H, W, 3]` | `uint8` | RGB channels unpacked from the renderer. |
| `depth` | `[B, H, W, 1]` | `float32` | Distance from the camera plane. |
| `segmentation` | `[B, H, W, 2]` | `int32` | Object id and MuJoCo object type; background is `(-1, -1)`. |

All camera sensors in one scene must share `use_textures`, `use_shadows`, and
`enabled_geom_groups` because there is one render context. If raycast and camera
geom groups differ, mjlab uses their union for the shared context and emits a
warning. Set `clone_data=True` when downstream code will mutate image tensors;
otherwise camera fields are zero-copy views into the render buffer.

Use `dr.cam_fovy` only for FOV-mode cameras. Cameras parameterized by physical
intrinsics (`sensorsize`/`focal`) use `dr.cam_intrinsic`; randomizing `cam_fovy`
will not change such rendered images.

## Verification ladder

- **CPU/config confidence:** import config classes, inspect signatures, construct
  dataclasses, and verify terrain preset names. This proves the API surface but
  not GPU sensor data.
- **CUDA/full sensor confidence:** instantiate a tiny scene with the relevant
  sensor, run `sim.forward()` or `sim.step()`, then `sim.sense()`, and assert
  shape/value signals (`distances >= 0` for expected ray hits, nonzero RGB for
  visible objects, contact `found > 0` for a settled contact). This is required
  before claiming camera/raycast/render-context behavior works.
- **Observation integration:** once sensor data is correct, route observation
  term wiring and group concatenation decisions to the manager/MDP sub-skills.
