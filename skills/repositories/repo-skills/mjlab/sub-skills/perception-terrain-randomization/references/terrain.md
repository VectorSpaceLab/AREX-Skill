# Terrain

mjlab treats terrain as a scene entity. A flat plane is enough for simple tasks;
procedural terrain is the standard choice for locomotion, navigation, terrain
curriculum, and flat-patch spawn workflows.

Use the bundled [`inspect_sensor_terrain.py`](../scripts/inspect_sensor_terrain.py)
helper when you need exact installed signatures or the current list of terrain
presets.

## Terrain entity choices

| Need | Config | Notes |
| --- | --- | --- |
| Flat ground | `TerrainEntityCfg(terrain_type="plane")` | Uses a MuJoCo plane-like ground with configurable environment spacing. |
| Procedural grid | `TerrainEntityCfg(terrain_type="generator", terrain_generator=...)` | Requires `TerrainGeneratorCfg` with at least one sub-terrain. |
| Curriculum start cap | `max_init_terrain_level` | Limits initial row sampling to easier rows. `None` allows all rows. |
| Visual debugging | `debug_vis=True` | Adds sites in groups 3, 4, and 5 for flat patches, env origins, and terrain origins. |

`SceneCfg.num_envs` should agree with the terrain's intended batch size; scene
construction can override the terrain entity's own `num_envs` so that terrain
origins match the scene batch.

```python
from mjlab.scene import SceneCfg
from mjlab.terrains import TerrainEntityCfg

scene = SceneCfg(
    num_envs=1024,
    env_spacing=4.0,
    terrain=TerrainEntityCfg(terrain_type="plane", env_spacing=4.0),
    entities={"robot": robot_cfg},
)
```

Route robot/entity construction details to the scene/assets sub-skill; this
reference only owns the terrain configuration itself.

## Procedural generator model

`TerrainGeneratorCfg` builds a rectangular grid of sub-terrain patches. Every
`SubTerrainCfg` shares `proportion`, `size`, and optional
`flat_patch_sampling`; individual subclasses add shape-specific parameters such
as stair width, obstacle count, slope range, noise range, or wave amplitude.

```python
from mjlab.terrains import TerrainEntityCfg
from mjlab.terrains import BoxPyramidStairsTerrainCfg, HfRandomUniformTerrainCfg
from mjlab.terrains import TerrainGeneratorCfg

rough_grid = TerrainEntityCfg(
    terrain_type="generator",
    max_init_terrain_level=5,
    terrain_generator=TerrainGeneratorCfg(
        seed=7,
        size=(8.0, 8.0),
        border_width=20.0,
        num_rows=10,
        curriculum=True,
        sub_terrains={
            "stairs": BoxPyramidStairsTerrainCfg(
                proportion=0.4,
                step_height_range=(0.0, 0.16),
                step_width=0.3,
                platform_width=2.0,
            ),
            "rough": HfRandomUniformTerrainCfg(
                proportion=0.6,
                noise_range=(0.02, 0.10),
                noise_step=0.02,
            ),
        },
        add_lights=True,
    ),
)
```

### Random vs curriculum mode

| Mode | Grid layout | Difficulty | Meaning of `proportion` |
| --- | --- | --- | --- |
| `curriculum=False` | `num_rows x num_cols`; every patch samples a type. | Sampled uniformly from `difficulty_range` per patch. | Patch sampling probability. |
| `curriculum=True` | `num_rows x len(sub_terrains)`; one column per terrain type. | Row 0 is easiest; final row is hardest. | Spawn distribution across terrain-type columns, not column count. |

In curriculum mode, `num_cols` is ignored for generated geometry. It should not
be used as the source of truth for the number of columns; use the number of
sub-terrains. Difficulty is linearly interpolated from `difficulty_range` by row.
With `num_rows=1`, the single row uses the lower difficulty bound.

Environment placement stores `terrain_levels` (row indices), `terrain_types`
(column indices), and `env_origins`. When proportions are available and match the
actual number of columns, envs are allocated with a largest-remainder method so
each column receives at least one env when `num_envs >= num_cols`. If no valid
proportion vector is available, envs are distributed evenly across columns.
Rows are sampled randomly up to `max_init_terrain_level` at initial placement.

## Terrain families

| Family | Classes/presets | Use when |
| --- | --- | --- |
| Flat primitive | `BoxFlatTerrainCfg`, preset `flat` | You need an easy baseline in a generated grid. |
| Stair primitives | `BoxPyramidStairsTerrainCfg`, `BoxInvertedPyramidStairsTerrainCfg`, `BoxRandomStairsTerrainCfg`, `BoxOpenStairsTerrainCfg` | Policies must learn step-up/down and structured stair traversal. |
| Obstacle primitives | `BoxRandomGridTerrainCfg`, `BoxRandomSpreadTerrainCfg`, `BoxSteppingStonesTerrainCfg`, `BoxNarrowBeamsTerrainCfg`, `BoxNestedRingsTerrainCfg`, `BoxTiltedGridTerrainCfg` | You need discrete obstacles, stones, beams, or tilted tiles. |
| Heightfields | `HfPyramidSlopedTerrainCfg`, `HfRandomUniformTerrainCfg`, `HfWaveTerrainCfg`, `HfDiscreteObstaclesTerrainCfg`, `HfPerlinNoiseTerrainCfg` | You need smooth slopes, random roughness, waves, or natural undulation. Heightfields support flat patch sampling. |

Primitive `Box*` terrains are built from geoms and are good for discrete
obstacles. Heightfield `Hf*` terrains are continuous elevation grids and are the
only built-in family that can compute flat patches.

## Named terrain sets

mjlab installs three ready-made `TerrainGeneratorCfg` bundles:

| Named config | Shape | Mode | Contents | Best use |
| --- | --- | --- | --- | --- |
| `ROUGH_TERRAINS_CFG` | size `(8, 8)`, `10 x 20` | random | flat, stairs, inverted stairs, slopes, inverted slopes, random rough, waves | Default rough locomotion variety. |
| `STAIRS_TERRAINS_CFG` | size `(8, 8)`, 10 rows | curriculum | flat plus easy, moderate, and challenging pyramid stairs | Stair-focused curriculum. |
| `ALL_TERRAINS_CFG` | size `(8, 8)`, 10 rows, one column per registered preset count in random mode | random | all terrain presets with equal proportion | Maximum variety and API smoke checks. |

Customize named configs with `dataclasses.replace()` or by replacing individual
sub-terrain entries:

```python
from dataclasses import replace
from mjlab.terrains.config import ROUGH_TERRAINS_CFG

small_rough = replace(ROUGH_TERRAINS_CFG, num_rows=5, difficulty_range=(0.1, 0.8))
```

Registered preset functions include `flat`, `pyramid_stairs`,
`pyramid_stairs_inv`, `hf_pyramid_slope`, `hf_pyramid_slope_inv`,
`random_rough`, `wave_terrain`, `discrete_obstacles`, `perlin_noise`,
`box_random_grid`, `random_spread_boxes`, `open_stairs`, `random_stairs`,
`stepping_stones`, `narrow_beams`, `nested_rings`, and `tilted_grid`. Prefer the
inspection script for the authoritative installed list.

## Flat patch sampling

Flat patches are named sets of safe spawn positions precomputed from heightfield
terrain. Configure them per sub-terrain with `flat_patch_sampling`:

```python
from mjlab.terrains import FlatPatchSamplingCfg, HfRandomUniformTerrainCfg

spawn_patch = FlatPatchSamplingCfg(
    num_patches=32,
    patch_radius=0.35,
    max_height_diff=0.04,
    x_range=(-3.0, 3.0),
    y_range=(-3.0, 3.0),
)

rough = HfRandomUniformTerrainCfg(
    proportion=1.0,
    noise_range=(0.02, 0.12),
    noise_step=0.02,
    flat_patch_sampling={"spawn": spawn_patch},
)
```

Runtime access:

```python
patches = env.scene.terrain.flat_patches["spawn"]
# Shape: [num_rows, num_cols, num_patches, 3]
```

Use `reset_root_state_from_flat_patches` as the reset event when the robot should
spawn on a sampled flat patch. That event falls back to the ordinary uniform
root-state reset when the terrain is absent or the named patch set is missing.
Route full event dictionary and reset lifecycle wiring to the manager/MDP
sub-skills.

Flat-patch constraints:

- Only `Hf*` terrain classes compute patches because the algorithm needs a
  height grid.
- The detector uses a circular footprint and accepts a candidate only when the
  max-min height variation is within `max_height_diff`.
- `grid_resolution` can be smaller than the terrain horizontal scale for finer
  boundary precision at higher preprocessing cost.
- If no valid pixels exist, the fallback is the sub-terrain center repeated to
  keep reset events valid.
- If any sub-terrain configures a patch name, storage is allocated for all grid
  cells; cells without patches use their origin as a valid placeholder.

## Terrain randomization and curriculum hooks

- `randomize_terrain(env, env_ids)` picks random terrain rows and columns for
  the selected environments. Use it for play/evaluation variety or reset-time
  random terrain assignment.
- `TerrainEntity.update_env_origins(env_ids, move_up, move_down)` advances or
  demotes curriculum levels and wraps over-hard environments to a random row.
  Built-in velocity curricula call this method after the first real reset, not
  on the initial reset.
- `TerrainEntityCfg.max_init_terrain_level` controls how difficult initial
  terrain rows can be. Increase this only after policies can survive harder
  starts.

## Debug visualization

Set `TerrainEntityCfg(debug_vis=True)` to add viewer-togglable sites:

| Group | Meaning | Typical use |
| --- | --- | --- |
| 3 | Flat patch sites | Check spawn candidate coverage and radius. |
| 4 | Environment origins | Verify parallel env placement. |
| 5 | Terrain origins | Verify generated sub-terrain grid layout. |

When combining terrain debug sites with raycasts or cameras, make sure the
sensor geom-group filters include or exclude groups intentionally. Debug groups
are for visualization and should not accidentally become policy-visible terrain
hits unless that is deliberate.

## Verification ladder

- CPU/config checks can instantiate `TerrainEntityCfg`, `TerrainGeneratorCfg`,
  preset functions, and pure sub-terrain configs.
- Pure terrain generation/compilation checks validate geometry definitions but
  are still not a full simulation rollout.
- CUDA/full checks are needed when the claim includes MuJoCo Warp simulation,
  raycast/camera sensing over generated terrain, or training-scale terrain
  curriculum behavior.
