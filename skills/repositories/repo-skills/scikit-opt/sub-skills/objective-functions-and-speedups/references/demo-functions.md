# Built-in demo functions

The package exposes benchmark functions under `sko.demo_func`. They are useful for quick optimizer checks and examples because they have no plotting, network, or external data requirement.

## Import pattern

```python
from sko.demo_func import sphere, schaffer, rosenbrock

value = sphere((0, 0, 0))
```

Each function follows the scalar objective contract: one candidate vector in, one scalar value out. If you want vectorization mode, wrap or rewrite the function so it accepts a population matrix and returns one value per row.

## Function catalog

| Function | Dimension pattern | Useful facts |
| --- | --- | --- |
| `sphere(p)` | n-D | Sum of squares; returns `0` at the all-zero vector. |
| `schaffer(p)` | 2-D | Multimodal 2-D benchmark; returns `0` at `(0, 0)`. |
| `shubert(p)` | 2-D | Many local minima; known low values around selected 2-D points. |
| `griewank(p)` | n-D | Multimodal benchmark; returns `0` at the all-zero vector. |
| `rastrigrin(p)` | n-D | Package spelling is `rastrigrin`; returns `0` at the all-zero vector. |
| `rosenbrock(p)` | n-D, usually >=2 | Valley-shaped benchmark; returns `0` at the all-one vector. |
| `sixhumpcamel(p)` | 2-D | Two-dimensional multimodal benchmark with negative global minima. |
| `zakharov(p)` | n-D | Returns `0` at the all-zero vector. |
| `ackley(p)` | 2-D package implementation | The package implementation returns `-200` at `(0, 0)`; do not assume a different textbook normalization. |
| `cigar(p)` | n-D | Ill-conditioned benchmark; returns `0` at the all-zero vector. |
| `function_for_TSP(num_points, seed=None)` | route fixture helper | Returns `(num_points, points_coordinate, distance_matrix, cal_total_distance)` for synthetic coordinates. Route workflow details belong to `../routing-and-combinatorial/`. |

## Tiny usage examples

Scalar objective in common mode:

```python
from sko.GA import GA
from sko.demo_func import sphere

ga = GA(func=sphere, n_dim=2, size_pop=6, max_iter=3, lb=[-1, -1], ub=[1, 1], precision=1e-2)
best_x, best_y = ga.run()
```

Vectorized wrapper for sphere-like behavior:

```python
import numpy as np
from sko.tools import set_run_mode

def sphere_vectorized(X):
    X = np.asarray(X, dtype=float)
    return np.sum(X * X, axis=1)

set_run_mode(sphere_vectorized, "vectorization")
```

Cached integer objective based on a demo function:

```python
from sko.demo_func import sphere
from sko.tools import set_run_mode

def cached_sphere(x):
    return float(sphere(tuple(x)))

set_run_mode(cached_sphere, "cached")
```

## Selection guidance

- Use `sphere` for a smooth correctness smoke.
- Use `schaffer`, `shubert`, `rastrigrin`, `griewank`, or `sixhumpcamel` when testing behavior on multimodal objectives.
- Use `rosenbrock` when testing optimizers on narrow-valley behavior.
- Use `cigar` when testing scale/conditioning sensitivity.
- Use `function_for_TSP` only as a helper for route algorithms; load the routing sub-skill before presenting TSP recipes or interpreting permutation routes.
