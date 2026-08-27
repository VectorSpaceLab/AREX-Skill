# Domain Randomization and Sensor Corruption

This reference covers robosuite visual and dynamics randomization, plus Observable-based sensor corruption and delay.

## Wrapper and modders

`robosuite.wrappers.DomainRandomizationWrapper` combines the modders below and can randomize on reset or every N steps:

| Component | What it changes | Main arguments |
| --- | --- | --- |
| `TextureModder` | geom colors, textures, materials, and skybox textures | `geom_names`, `randomize_local`, `randomize_material`, `texture_variations`, `randomize_skybox` |
| `CameraModder` | camera position, rotation, and fovy | `camera_names`, `randomize_position`, `randomize_rotation`, `randomize_fovy` |
| `LightingModder` | light position, direction, specular, ambient, diffuse, and active state | `light_names`, `randomize_position`, `randomize_direction`, `randomize_specular`, `randomize_ambient`, `randomize_diffuse`, `randomize_active` |
| `DynamicsModder` | body, geom, joint, and global dynamics parameters | `body_names`, `geom_names`, `joint_names`, and the matching `randomize_*` toggles |

Wrapper-level controls:

- `seed`
- `randomize_on_reset`
- `randomize_every_n_steps`
- `randomize_color`
- `randomize_camera`
- `randomize_lighting`
- `randomize_dynamics`

Recommended usage patterns:

- set `randomize_every_n_steps=0` for manual randomization
- keep `randomize_camera=False` if you want stable visual demos or videos
- call `save_default_domain()` / `restore_default_domain()` when you want to snapshot and recover the base domain

### Version caveat

`TextureModder` in this repo version requires `mujoco==3.1.1` when `randomize_color=True`. If you are on a newer MuJoCo build, disable color randomization by setting `randomize_color=False`.

## Observable-based sensor corruption

robosuite `Observable` objects model a realistic sensor pipeline:

1. raw sensor value from `sensor`
2. optional corruption through `corrupter`
3. optional post-processing through `filter`
4. optional delay through `delayer`
5. discrete update frequency through `sampling_rate`

Runtime controls:

- `env.modify_observable(observable_name=..., attribute=..., modifier=...)`
- `env.add_observable(...)`
- `Observable(..., enabled=True, active=True)`

Common camera and proprioception corruption patterns:

- Gaussian pixel or state noise with `create_gaussian_noise_corrupter`
- random delay with `create_uniform_sampled_delayer`
- a custom `filter` to record delayed values or smooth sensor streams

## Minimal sensor-realism pattern

```python
from robosuite.utils.observables import create_gaussian_noise_corrupter, create_uniform_sampled_delayer

env.modify_observable(
    observable_name="frontview_image",
    attribute="corrupter",
    modifier=create_gaussian_noise_corrupter(mean=0.0, std=5.0, low=0, high=255),
)
env.modify_observable(
    observable_name="frontview_image",
    attribute="delayer",
    modifier=create_uniform_sampled_delayer(min_delay=0.02, max_delay=0.06),
)
```

Use the same `Observable` API to recreate this pattern in your own task code, and keep teleoperation-specific capture flows in `../teleoperation`.
