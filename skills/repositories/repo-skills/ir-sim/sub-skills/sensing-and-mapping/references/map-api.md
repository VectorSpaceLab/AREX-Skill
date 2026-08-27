# Occupancy, fog, and planner-map API

## World configuration

The `world.obstacle_map` value accepts `null`, a NumPy array in Python, an
image path string, or a generator dictionary. The canonical YAML forms are:

```yaml
world:
  width: 20
  height: 15
  offset: [-2, 1]
  obstacle_map:
    name: perlin
    resolution: 0.25
    complexity: 0.12
    fill: 0.32
    fractal: 1
    attenuation: 0.5
    seed: 48
  mdownsample: 1
  fog_map: true
  fog_map_resolution: 0.25
```

A string is shorthand for `{name: image, path: <string>}`. `World.gen_grid_map`
returns `(grid_map, obstacle_index, obstacle_positions)` and stores the grid in
`world.grid_map`; a cell is occupied when its value is greater than `50`.
`obstacle_index` is the two-row result of `np.where(grid_map > 50)`, and
`obstacle_positions` contains occupied cell centers in world coordinates,
including `world.offset`.

`mdownsample` is applied by the world after resolution of an image, array, or
procedural generator. In the 2.10.2 implementation it is Python slicing
`grid[::mdownsample, ::mdownsample]`: it is subsampling, not a block-max
operation. The resulting cell sizes are recomputed as
`width / grid.shape[0]` and `height / grid.shape[1]`, so do not carry forward
the generator's nominal resolution after downsampling. Keep this distinction
in mind when matching a planner map to collision behavior. For conservative
coarsening at planner request time, use `World.get_map`, described below.

## Built-in generators and resolve/build APIs

The live signatures are:

```text
resolve_obstacle_map(obstacle_map=None, world_width=None, world_height=None)
build_grid_from_generator(spec, world_width, world_height)
ImageGridGenerator(path, **kwargs)
PerlinGridGenerator(width, height, complexity=0.142857, fill=0.38,
                    fractal=1, attenuation=0.5, seed=None)
GridMapGenerator.generate() -> generator
GridMapGenerator.save_as_image(filepath, invert=True)
```

Use `resolve_obstacle_map` for the same dispatch as `World`:

- `None` returns `None`.
- An ndarray is returned as float64.
- A string is treated as an image path.
- An image dictionary requires `name: image` and a non-empty `path`; its grid
  dimensions come from the image, not world dimensions or `resolution`.
- A non-image dictionary must include a registered `name`, `resolution`, and
  world width/height. Missing world dimensions or resolution raises `ValueError`;
  unsupported input types raise `TypeError`.

`build_grid_from_generator` computes cell dimensions as
`(max(1, round(world_width / resolution)), max(1, round(world_height /
resolution)))`. It passes only constructor names listed by the generator's
`yaml_param_names`; unlisted extra YAML keys are ignored. Built-ins are
registered as `image` and `perlin` when `irsim.world.map` is imported.

### Image maps

`ImageGridGenerator` reads a grayscale or RGB/RGBA image, normalizes integer
pixels or values above one, converts RGB with the package's luminance weights,
and maps it to occupancy `100 * (1 - grayscale)`. Thus dark pixels become
occupied and light pixels free. The returned array is transposed and flipped
left-right (`np.fliplr(grid.T)`) to align image coordinates with the world
array. Image dimensions are pixel dimensions after that transform. Paths are
resolved through IR-SIM's package/script path helper; in portable runtime
configs provide an explicit input path that exists in the caller's project.
Do not rely on an example checkout or package test image.

### Perlin maps

`PerlinGridGenerator` generates a deterministic binary-like grid of `0.0` and
`100.0`. `seed` makes repeated constructions identical; omitted seed varies.
`fill` controls the approximate occupied fraction (larger fill means more
obstacles), `complexity` changes feature scale, `fractal` adds octave detail and
must be at least one, and `attenuation` must be positive. The direct generator
constructor takes **cell counts**, while YAML `resolution` takes metres per
cell and the framework derives those counts from world dimensions. Do not put
`width`/`height` cell counts in the YAML generator spec.

```python
from irsim.world.map import PerlinGridGenerator, build_grid_from_generator

generator = PerlinGridGenerator(32, 24, fill=0.25, seed=7).generate()
assert generator.grid.shape == (32, 24)
grid = build_grid_from_generator(
    {"name": "perlin", "resolution": 0.25, "fill": 0.25, "seed": 7},
    world_width=8.0,
    world_height=6.0,
)
assert grid.shape == (32, 24)
```

## Map container, resolution, and collision

`env.get_map(resolution=0.1)` returns a `Map` carrying `width`, `height`,
requested `resolution`, `grid`, `obstacle_list`, and `world_offset`. The
constructor is:

```text
Map(width=10, height=10, resolution=0.1, obstacle_list=None,
    grid=None, world_offset=None)
```

`map.grid_resolution` reports actual `(width/grid.shape[0],
height/grid.shape[1])`, or `None` when no grid exists. When a grid exists and
requested `resolution` differs from its x cell size by more than 5%, `Map`
warns; grid-based planners should use `grid_resolution` for indexing.

`World.get_map` handles resolution relative to the world's existing grid:

- A non-positive or non-finite request warns and falls back to current grid
  resolution.
- A request more than 5% coarser invokes an internal conservative downsampler:
  each output cell is the maximum of the fine cells it covers, preserving any
  obstacle in a block, and emits a warning.
- A request more than 5% finer emits a warning and does not upsample; the
  original grid and its actual grid resolution are used.
- Near-equal requests leave the grid unchanged.

`Map.grid_occupied(x, y, margin_x=0, margin_y=0, threshold=50)` returns
`None` without a grid, otherwise a bool. It treats points outside the
`world_offset`-shifted world bounds as occupied. Positive margins expand the
cell neighborhood checked. `Map.is_collision(geometry)` treats out-of-bounds
geometry as collision, checks occupied grid cells first, then falls back to
Shapely intersections against `obstacle_list` when the grid is free or absent.
Grid collision uses occupied cell centers and a half-cell collision radius;
values `>50` are occupied. This is a coarse lookup, not exact polygon raster
intersection.

For navigation, construct the map once and pass it to the selected planner;
use the same map resolution and `world_offset` assumptions throughout. The
planner route owns planner constructors, path output, and `None`/blocked-map
handling:

```python
env_map = env.get_map(resolution=0.2)
# planner-specific constructor and planning() belong to navigation-and-planning
```

A coarser request can be safer but less geometrically detailed; a finer request
cannot manufacture detail that was removed by `mdownsample`. If a planner's
map/grid dimensions and collision lookups disagree, inspect
`env_map.grid.shape`, `env_map.grid_resolution`, `env_map.resolution`, and
`env_map.world_offset` before changing planner iterations or robot radius.

## FogMap and exploration

`world.fog_map: true` creates a `FogMap`; `fog_map_resolution` is its cell size.
When omitted, the world uses the obstacle grid's current x cell size, or `0.1`
m when there is no obstacle map. The constructor is:

```text
FogMap(width=10, height=10, resolution=0.1, world_offset=None)
```

It validates that resolution is positive and finite. `fog.shape` is
`(round(width/resolution), round(height/resolution))` with a minimum of one per
axis; `fog.explored` is a boolean mask initially all false, and
`fog.explored_ratio` is its mean. Fog is an exploration overlay, not an
occupancy grid: it subclasses `Map`, but has no `grid`, so its `grid_occupied`
method returns `None`.

```python
fog.reveal_from_lidar(origin, angles, ranges)
fog.reveal_fov(origin, fov, fov_radius)
fog.reset()
rgba = fog.to_rgba()  # (nx, ny, 4), transpose for imshow
```

`reveal_from_lidar` samples each beam at half a fog-cell step, clamps each beam
to its own measured range, and marks in-bounds cells along line of sight. Empty
or non-positive ranges are no-ops. `reveal_fov` marks cells in a circular
sector but has no occlusion; `origin` is `[x, y, theta]` (theta optional),
`fov` is the full angle, and non-positive angle/radius is a no-op. The world
calls the appropriate reveal method after synchronized sensor updates: LiDAR
wins when present; otherwise explicit object FOV is used. `fog.reset()` clears
the mask and `to_rgba()` gives unexplored cells an alpha while explored cells
become transparent. Rendering helpers are optional; the mask works headlessly.
