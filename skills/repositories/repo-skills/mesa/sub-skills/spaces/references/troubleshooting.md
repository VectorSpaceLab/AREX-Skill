# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'scipy'` while building grids or continuous space | SciPy is missing from the environment | Install SciPy; `KDTree` and `cdist` are used by grid, network, voronoi, and continuous lookup paths. |
| `ModuleNotFoundError: No module named 'networkx'` when constructing `Network(..., layout=None)` | The default layout path imports `networkx` | Install `networkx`, or pass a graph-like object plus an explicit layout mapping/callable. |
| `ValueError: Dimensions must be a list of positive integers.` | Grid dimensions contain non-positive or non-integer values | Pass positive integers for every dimension. |
| `TypeError: Torus must be a boolean.` | `torus` is not a real bool | Pass `True` or `False`. |
| `ValueError: HexGrid with torus=True requires both width and height to be even.` | Hex torus geometry needs even side lengths | Use even dimensions or disable torus wrapping. |
| `ValueError: Array shape ... does not match grid dimensions ...` | A property layer array does not match the grid shape | Create the array with the exact grid dimensions before attaching it. |
| `ValueError: property_layer '...' conflicts with an existing Grid attribute.` | The property-layer name overlaps an existing grid attribute | Choose a different layer name. |
| `AttributeError` when assigning a read-only layer on a cell | The accessor was created with `read_only=True` | Mutate `grid.property_layers[name]` in place, or create a writable layer if cell-level assignment is needed. |
| `CellFullException` while placing an agent | The destination cell reached capacity | Choose from `cells_with_capacity`, lower the occupancy, or raise the capacity. |
| `IndexError: No available cells exist in the grid: all cells are at full capacity.` | `select_random_cell_with_capacity()` exhausted every cell | Increase capacity or release agents first. |
| `LookupError` from `CellCollection.select_random_cell()` or `select_random_agent()` | The collection is empty | Guard the empty case or pass a default value. |
| `ValueError: No cell in direction ...` from `Grid2DMovingAgent.move(...)` | The direction name is invalid or the cell is not connected that way | Use a supported alias (`north`, `south`, `east`, `west`, etc.) and confirm the target cell is connected. |
| `ValueError` when moving a `FixedAgent` | A fixed agent can only be assigned once | Use `CellAgent` for mobile agents, or create a new `FixedAgent` for a different location. |
| `SpaceException` from `Network` | The layout mapping does not include every node | Provide a position for every graph node. |
| `ValueError` from `ContinuousSpaceAgent.position = ...` | The point is outside the bounds of a non-torus space | Clamp the coordinate, switch to `torus=True`, or pick a point inside the domain. |
| `UserWarning` about `k` being larger than the population | The continuous-space nearest-neighbor query asked for more agents than exist | Lower `k`, or treat the returned full population as the valid result. |
| `ValueError` from `cell.get_neighborhood(radius=0)` | Neighborhood radii start at 1 | Use `radius >= 1`. |

## Quick fixes

### Preserve property-layer links

```python
# Good: in-place mutation keeps the cell accessor attached.
grid.property_layers["sugar"][:] += 1

# Bad: rebinding breaks the link.
grid.sugar = np.zeros((4, 4))
```

### Keep `cells_with_capacity` and `empties` straight

```python
if cell in grid.empties:
    # zero occupancy
    ...

if cell in grid.cells_with_capacity:
    # still has room for another agent
    ...
```

### Keep `networkx` optional

```python
try:
    import networkx as nx
except ModuleNotFoundError:
    nx = None

if nx is not None:
    graph = nx.path_graph(3)
    layout = {0: (0.0, 0.0), 1: (1.0, 0.0), 2: (2.0, 0.0)}
    net = Network(graph, layout=layout, random=rng)
```

## Things to check first

1. `scipy` is installed.
2. `torus` is a boolean.
3. Grid shapes and property-layer shapes match exactly.
4. You are mutating property layers in place, not rebinding them.
5. `networkx` is only imported when you actually need it.
6. You are using `mesa.experimental.continuous_space`, not legacy `mesa.space`.
