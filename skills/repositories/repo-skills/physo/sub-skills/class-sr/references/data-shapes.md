# ClassSR data shapes

## Core dataset contract

`physo.ClassSR` consumes multiple realizations of the same phenomenon.

### `multi_X`
- type: list-like
- length: `n_realizations`
- each element: array-like of shape `(n_dim, n_samples_i)`
- requirement: every realization must use the same `n_dim`
- allowed: different `n_samples_i` values across realizations

### `multi_y`
- type: list-like
- length: `n_realizations`
- each element: array-like of shape `(n_samples_i,)`
- requirement: each `multi_y[i]` must match `multi_X[i]` in sample count

### `multi_y_weights`
Accepted forms:
1. a single scalar, broadcast to every realization
2. a length-`n_realizations` list/array of scalars, one scalar per realization
3. a length-`n_realizations` list/array of per-point arrays, where each array has shape `(n_samples_i,)`

Shape rule:
- if weights are per-point, `multi_y_weights[i].shape == multi_y[i].shape`
- if weights are per-realization scalars, each scalar is expanded to a constant vector for that realization

## Constant contracts

### `class_free_consts_names` / `class_free_consts_units` / `class_free_consts_init_val`
- one entry per class free constant
- all three containers must agree in length
- class constants are shared across all realizations
- `class_free_consts_init_val` is passed positionally in the same order as the names
- the wrapper expects list-like / array-like init values, even though lower-level tokenization helpers can accept name-keyed mappings

### `spe_free_consts_names` / `spe_free_consts_units` / `spe_free_consts_init_val`
- one entry per realization-specific constant
- all three containers must agree in length
- spe constants are optimized separately for each realization
- `spe_free_consts_init_val` is passed positionally in the same order as the names
- the wrapper expects list-like / array-like init values, even though lower-level tokenization helpers can accept name-keyed mappings
- `spe_free_consts_init_val` may be:
  - a scalar per constant, broadcast to every realization
  - a length-`n_realizations` vector per constant

### Units
- keep units consistent across inputs, outputs, and constants
- use dimensionless units for all terms when the problem is not physics-aware
- if units are missing for a non-empty constant list, the package assumes dimensionless units

## Example layout

```python
multi_X = [
    np.stack((x0_a,), axis=0),   # (1, n_a)
    np.stack((x0_b,), axis=0),   # (1, n_b)
]
multi_y = [y_a, y_b]             # (n_a,), (n_b,)
multi_y_weights = [
    np.linspace(1.0, 2.0, len(y_a)),
    np.ones_like(y_b),
]

class_free_consts_names = ["c0"]
class_free_consts_units = [[0, 0, 0]]
class_free_consts_init_val = {"c0": 1.0}

spe_free_consts_names = ["k0"]
spe_free_consts_units = [[0, 0, 0]]
spe_free_consts_init_val = {"k0": [0.5, -0.25]}
```

## Output shapes to remember

After a successful run:
- `best_expr.free_consts.class_values.shape == (1, n_class_free_consts)`
- `best_expr.free_consts.spe_values.shape == (1, n_spe_free_consts, n_realizations)`
- `best_expr.get_infix_sympy(evaluate_consts=True)` returns one sympy expression per realization

## Common mistakes

- Using `SR`-style single-dataset arrays instead of lists of realizations
- Giving one `X` or `y` array for all realizations instead of one per realization
- Passing per-point weights whose length does not match the corresponding `y`
- Passing a spe constant initial-value vector whose length does not match `n_realizations`
- Mismatching the number of free-constant names and unit vectors
- Mixing devices when inputs are already torch tensors
