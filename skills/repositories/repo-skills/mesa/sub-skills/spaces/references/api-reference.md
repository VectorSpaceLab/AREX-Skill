# API Reference

## Verified baseline

- Mesa version: **4.0.0a0**
- Python: **3.12+**
- Space code uses SciPy-backed spatial lookup helpers.
- `Network` can work without `networkx` imports in your code if you provide your own graph-like object and layout; the default `layout=None` path imports `networkx` for a circular layout.

## Import surface

```python
from mesa.discrete_space import (
    Cell,
    CellAgent,
    CellCollection,
    DiscreteSpace,
    FixedAgent,
    Grid,
    Grid2DMovingAgent,
    HexGrid,
    Network,
    OrthogonalMooreGrid,
    OrthogonalVonNeumannGrid,
    VoronoiGrid,
)
from mesa.experimental.continuous_space import ContinuousSpace, ContinuousSpaceAgent
```

## Object map

```text
mesa.discrete_space
├─ Cell
├─ CellAgent
├─ FixedAgent
├─ Grid2DMovingAgent
├─ CellCollection
├─ DiscreteSpace
├─ Grid
├─ OrthogonalMooreGrid
├─ OrthogonalVonNeumannGrid
├─ HexGrid
├─ Network
└─ VoronoiGrid

mesa.experimental.continuous_space
├─ ContinuousSpace
└─ ContinuousSpaceAgent
```

## Class choice table

| Pick this class | Use it when | Key caveat |
| --- | --- | --- |
| `Cell` | You need a single location object or custom connectivity | Base occupancy is a plain attribute until a grid overrides it |
| `CellCollection` | You need to filter or sample a group of cells | Empty collections raise unless you pass a default |
| `CellAgent` | You need a mobile agent that lives on a cell | Cell assignment is atomic and respects capacity |
| `FixedAgent` | You need an immobile patch or node occupant | The cell can only be assigned once |
| `Grid2DMovingAgent` | You want named 2D directions like north/east | It only helps with 2D move commands |
| `OrthogonalMooreGrid` | You need 8-neighbor or `3^n-1` adjacency | Diagonals are included |
| `OrthogonalVonNeumannGrid` | You need orthogonal-only adjacency | No diagonal neighbors |
| `HexGrid` | You need a hex lattice | `torus=True` requires even dimensions |
| `Network` | You need graph topology or node-based movement | `layout=None` imports `networkx` |
| `VoronoiGrid` | You need irregular regions from seed points | Uses centroid geometry and per-cell polygon metadata |
| `ContinuousSpace` | You need experimental continuous coordinates | API is still experimental |
| `ContinuousSpaceAgent` | You need an agent with a continuous `position` | Movement uses positions, not cells |

## `Cell`

```python
Cell(coordinate, position=None, capacity=None, random=None)
```

Key behavior:

- `coordinate` is the logical key used by spaces.
- `position` is the physical coordinate array; if omitted, the cell defaults to `np.asarray(coordinate, dtype=float)`.
- `capacity=None` means unlimited occupancy.
- `connect(other, key=None)` adds a one-way connection. Space classes add both directions when needed.
- `disconnect(other)` removes every edge pointing at that cell and raises `ConnectionMissingException` if no edge exists.
- `add_agent(agent)` raises `CellFullException` when the cell is full.
- `remove_agent(agent)` raises `AgentMissingException` when the agent is absent.
- `empty` is initialized on construction and stays in sync with occupancy; grid cells override it with a property layer.
- `is_empty` and `is_full` are computed from the live agent list.
- `agents` returns a copy of the current agent list.
- `neighborhood` is shorthand for `get_neighborhood(radius=1)`.
- `get_neighborhood(radius=1, include_center=False)` returns a `CellCollection`.
- `radius < 1` raises `ValueError`.

## `CellCollection`

```python
CellCollection(cells, random=None)
```

- Accepts either a mapping of `Cell -> list[CellAgent]` or an iterable of cells.
- `cells` returns a cached list of the collection members.
- `agents` iterates over every agent across every cell.
- `select_random_cell(default=RAISES)` raises `LookupError` when empty unless a default is provided.
- `select_random_agent(default=RAISES)` does the same for agents.
- `select(filter_func=None, at_most=float("inf"))` filters cells.
  - A float `at_most <= 1.0` is treated as a fraction of the collection length.
  - `filter_func=None` and `at_most=inf` returns the original collection.
- `random=None` emits a reproducibility warning and falls back to a new `Random()` instance.

## `DiscreteSpace`

```python
DiscreteSpace(capacity=None, cell_klass=Cell, random=None)
```

- Base class for all discrete spaces.
- `all_cells` returns a `CellCollection` over every current cell.
- `agents` returns an `AgentSet` view over agents in the space.
- `empties` filters `all_cells` by `cell.is_empty`.
- `add_cell(cell)` silently overwrites any cell already stored at the same coordinate.
- `remove_cell(cell)` removes the cell and disconnects its neighbors.
- `add_connection(cell1, cell2)` adds bidirectional connections.
- `remove_connection(cell1, cell2)` removes bidirectional connections.
- `select_random_empty_cell()` chooses from `empties` and may raise `IndexError` if none exist.
- `__getitem__(coordinate)` returns the cell or raises `CellMissingException`.
- `__setstate__` relinks cell connections after pickle/deepcopy round trips.

## `Grid`

```python
Grid(dimensions, torus=False, capacity=None, random=None, cell_klass=Cell)
```

`Grid` is the concrete base for regular grids and the owner of property layers.

### Property layers

```python
create_property_layer(name, default_value=0.0, dtype=float, read_only=False)
add_property_layer(name, array, read_only=False)
remove_property_layer(name)
```

- `create_property_layer` creates a NumPy array with the grid dimensions and attaches cell accessors.
- `add_property_layer` attaches an existing array; the array shape must exactly match `dimensions`.
- `remove_property_layer` removes the mapping and cell accessor.
- Rebinding `grid.<layer>` breaks the link. Mutate the array in place instead.
- `read_only=True` installs a cell accessor with no setter; the backing array is still stored in `grid.property_layers[name]`.
- `Grid.__setstate__` restores read-only and writable accessors after pickle/deepcopy.

### Capacity helpers

- `cells_with_capacity` returns cells where `not cell.is_full`.
- If `capacity is None`, every cell is available.
- `select_random_cell_with_capacity()` chooses a non-full cell and raises `IndexError` when every cell is full.

### Spatial helpers

- `find_nearest_cell(position)` floors to a coordinate and wraps when `torus=True`.
- `get_neighborhood_mask(coordinate, include_center=True, radius=1)` returns a boolean mask.
- `select_random_empty_cell()` has a fast random path and a fallback scan through the `empty` layer.

## `OrthogonalMooreGrid`

```python
OrthogonalMooreGrid(dimensions, torus=False, capacity=None, random=None, cell_klass=Cell)
```

- 8 neighbors in 2D.
- `3^n - 1` neighbors in nD.
- Good for dense movement and diagonal adjacency.

## `OrthogonalVonNeumannGrid`

```python
OrthogonalVonNeumannGrid(dimensions, torus=False, capacity=None, random=None, cell_klass=Cell)
```

- 4 neighbors in 2D.
- `2n` neighbors in nD.
- Good for orthogonal-only movement.

## `HexGrid`

```python
HexGrid(dimensions, torus=False, capacity=None, random=None, cell_klass=Cell)
```

- 2D only.
- Six-neighbor hexagonal adjacency.
- `torus=True` requires both dimensions to be even.
- Uses pointy-topped physical positioning and KD-tree nearest-cell lookup.

## `Network`

```python
Network(G, capacity=None, random=None, cell_klass=Cell, layout=None)
```

- `G` must provide `.nodes` and `.neighbors` like a NetworkX graph.
- `layout` may be a mapping or a callable returning node positions.
- If `layout is None`, Mesa imports `networkx` and uses `nx.circular_layout`.
- Missing node IDs in the layout raise `SpaceException`.
- Non-mapping/non-callable `layout` raises `TypeError`.
- `find_nearest_cell(position)` uses a KD-tree and rebuilds lazily after spatial mutations.
- `add_cell` / `remove_cell` update the backing graph and mark spatial caches dirty when the cell has a physical position.
- `add_connection` / `remove_connection` keep the graph edges synchronized with the cell connections.

## `VoronoiGrid`

```python
VoronoiGrid(centroids_coordinates, capacity=None, random=None, cell_klass=Cell)
```

- `centroids_coordinates` must be a homogeneous sequence of coordinate sequences.
- All centroids must have the same dimensionality.
- The implementation uses 2D Delaunay/Voronoi geometry.
- Each cell coordinate is an integer index; the physical centroid is stored in `cell.position`.
- Each cell gets `properties["polygon"]` and `properties["area"]`.
- `capacity` may be numeric or a callable that maps polygon area to capacity.
  - Numeric capacity is applied uniformly.
  - Callable capacity is evaluated per cell from the polygon area.
  - `None` leaves capacities unlimited.
- `find_nearest_cell(position)` uses a KD-tree over centroid positions.

## `ContinuousSpace`

```python
ContinuousSpace(dimensions, torus=False, random=None, n_agents=100)
```

- `dimensions` is an array-like of `[min, max]` pairs.
- `ndims` is derived from the number of rows in `dimensions`.
- `size` and `center` are derived from the bounds.
- `agent_positions` is a view into the live NumPy storage.
- `_add_agent` grows the backing array automatically when needed.
- `_remove_agent` swaps the last agent into the removed slot to keep the arrays compact.
- `calculate_difference_vector(point, agents=None)` returns shortest deltas, including torus wrapping when enabled.
- `calculate_distances(point, agents=None, **kwargs)` returns `(distances, agents)`.
- `get_agents_in_radius(point, radius=1)` filters by distance.
- `get_k_nearest_agents(point, k=1)`:
  - returns `([], array([]))` when the space is empty or `k <= 0`
  - warns and returns every agent when `k` exceeds the population
- `in_bounds(point)` checks the coordinate bounds.
- `torus_correct(point)` wraps a point into the space bounds.
- Convenience properties: `x_min`, `x_max`, `y_min`, `y_max`, `width`, `height`.

## `ContinuousSpaceAgent`

```python
ContinuousSpaceAgent(space, model)
```

- Registers itself with the `ContinuousSpace` on construction.
- `position` reads and writes directly into the space's position array.
- Non-torus assignment outside the bounds raises `ValueError`.
- Torus assignment wraps automatically.
- `remove()` removes the agent from both the model and the continuous space.
- `get_neighbors_in_radius(radius=1)` excludes the agent itself.
- `get_nearest_neighbors(k=1)` requests `k + 1` neighbors from the space and then excludes the agent itself.

## Cross-cutting notes

- `capacity=None` means unlimited occupancy across all space types.
- `cells_with_capacity` is not the same as `empties`.
  - `empties` means zero agents.
  - `cells_with_capacity` means not full, even if partially occupied.
- Keep `networkx` optional in user code, but treat `scipy` as required for the spatial lookup helpers in this sub-skill.
- Use `mesa.experimental.continuous_space`, not `mesa.space`, for continuous movement.
