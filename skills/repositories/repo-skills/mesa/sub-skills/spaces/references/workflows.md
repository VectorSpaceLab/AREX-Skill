# Workflows

## 1) Build a finite-capacity grid with property layers

Use this pattern when agents need to share cells up to a limit and the environment carries mutable state.

```python
import numpy as np
import mesa
from mesa.discrete_space import CellAgent, OrthogonalMooreGrid

model = mesa.Model(rng=42)
grid = OrthogonalMooreGrid((4, 4), torus=False, capacity=2, random=model.random)

sugar = grid.create_property_layer("sugar", default_value=1.0)
grid.add_property_layer("moisture", np.zeros((4, 4), dtype=float))
protected = grid.create_property_layer("protected", default_value=5.0, read_only=True)

sugar[:] += 1.0                 # in-place mutation keeps accessors alive
grid[0, 0].sugar += 2  # per-cell mutation still updates the array

agent_a = CellAgent(model)
agent_b = CellAgent(model)
agent_a.move_to(grid[0, 0])
agent_b.move_to(grid[0, 0])
```

Validation signals:

- `grid[0, 0].sugar` reflects the NumPy array value.
- `grid[0, 0]` leaves `empties` after the first agent arrives.
- `grid[0, 0]` leaves `cells_with_capacity` after reaching capacity.
- `grid[0, 0].protected = 9` raises `AttributeError`.
- `grid.add_property_layer("bad", np.zeros((2, 2)))` raises `ValueError`.
- `grid.create_property_layer("width")` raises `ValueError` because the name conflicts with an existing grid attribute.

## 2) Choose the right occupancy query

Use `empties` only when you need zero-occupancy cells. Use `cells_with_capacity` when partially full cells are still valid targets.

```python
cell = grid.select_random_empty_cell()
if cell not in grid.empties:
    raise RuntimeError("expected an empty cell")

free_cell = grid.select_random_cell_with_capacity()
if free_cell.is_full:
    raise RuntimeError("expected a non-full cell")
```

Validation signals:

- A cell with one of two slots filled is not empty, but it is still in `cells_with_capacity`.
- A cell at full capacity disappears from `cells_with_capacity`.
- `select_random_cell_with_capacity()` raises `IndexError` if every cell is full.

## 3) Work with the neighborhood families

Use Moore, Von Neumann, and Hex grids when the neighborhood shape matters.

```python
from mesa.discrete_space import HexGrid, OrthogonalMooreGrid, OrthogonalVonNeumannGrid

moore = OrthogonalMooreGrid((4, 4), torus=False, random=model.random)
vonneumann = OrthogonalVonNeumannGrid((4, 4), torus=False, random=model.random)
hexgrid = HexGrid((4, 4), torus=True, random=model.random)

center = moore[1, 1]
moore_neighbors = center.neighborhood
wide = center.get_neighborhood(radius=2, include_center=True)
```

Validation signals:

- Moore grids include diagonal neighbors.
- Von Neumann grids only include orthogonal neighbors.
- `HexGrid(torus=True)` requires even dimensions.
- `get_neighborhood(radius=0)` raises `ValueError`.

## 4) Use graph-backed or irregular spaces

### Network

Use `Network` when the topology comes from a graph instead of a geometric grid.

```python
import mesa
import networkx as nx
import numpy as np
from mesa.discrete_space import Network

model = mesa.Model(rng=42)
G = nx.path_graph(3)
layout = {0: (0.0, 0.0), 1: (1.0, 0.0), 2: (2.0, 0.0)}
net = Network(G, layout=layout, random=model.random)

closest = net.find_nearest_cell(np.array([1.2, 0.0]))
```

### Voronoi

Use `VoronoiGrid` when cells should be built around irregular seed points.

```python
import mesa
from mesa.discrete_space import VoronoiGrid

model = mesa.Model(rng=42)
points = [[0.0, 0.0], [1.0, 0.0], [0.5, 1.0], [1.5, 1.0], [0.0, 2.0], [1.0, 2.0]]
voro = VoronoiGrid(points, capacity=lambda area: max(1, int(area)), random=model.random)
cell = voro.find_nearest_cell([0.5, 1.0])
```

Validation signals:

- `Network` accepts a mapping or callable layout.
- Missing layout entries raise `SpaceException`.
- `VoronoiGrid` cells carry `properties["polygon"]` and `properties["area"]`.
- Callable capacity functions are invoked per cell from polygon area.

## 5) Move agents in 2D grids

Use `CellAgent` for general movement, `FixedAgent` for immobile placement, and `Grid2DMovingAgent` for direction names.

```python
import mesa
from mesa.discrete_space import Cell, FixedAgent, Grid2DMovingAgent, OrthogonalMooreGrid

model = mesa.Model(rng=42)
grid = OrthogonalMooreGrid((4, 4), random=model.random)

mover = Grid2DMovingAgent(model)
mover.cell = grid[1, 1]
mover.move("north")

fixed = FixedAgent(model)
fixed.cell = Cell((99,), random=model.random)
```

Validation signals:

- `Grid2DMovingAgent.move("north")` changes cells by one step.
- An invalid direction raises `ValueError`.
- `FixedAgent` cannot be reassigned after its first placement.
- `FixedAgent.remove()` clears the cell reference.

## 6) Query subsets with `CellCollection`

Use `CellCollection` when a workflow needs a reusable set of cells rather than a raw list.

```python
subset = grid.all_cells.select(lambda cell: cell.coordinate[0] == 0, at_most=2)
choice = subset.select_random_cell()

occupied = subset.select(lambda cell: not cell.is_empty)
agent = occupied.select_random_agent(default=None)
```

Validation signals:

- `select()` preserves the `CellCollection` API.
- `select_random_cell()` and `select_random_agent()` draw only from the collection members.
- Empty collections raise `LookupError` unless a default is supplied.

## 7) Use experimental continuous space

Use `ContinuousSpace` when agents move in continuous coordinates instead of discrete cells.

```python
import mesa
import numpy as np
from mesa.experimental.continuous_space import ContinuousSpace, ContinuousSpaceAgent

model = mesa.Model(rng=42)
space = ContinuousSpace(np.array([[0.0, 1.0], [0.0, 1.0]]), torus=True, random=model.random)
a1 = ContinuousSpaceAgent(space, model)
a2 = ContinuousSpaceAgent(space, model)
a1.position = [0.1, 0.1]
a2.position = [0.9, 0.1]

near = a1.get_nearest_neighbors(k=1)
within = a1.get_neighbors_in_radius(0.3)
```

Validation signals:

- Torus spaces wrap positions automatically.
- Non-torus spaces raise `ValueError` when a position is out of bounds.
- `get_nearest_neighbors` excludes the agent itself.
- `get_k_nearest_agents` warns when `k` exceeds the population and still returns every agent.
- `remove()` keeps `active_agents`, `agent_positions`, and the model registry in sync.
