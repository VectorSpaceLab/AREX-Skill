# API reference

Validated against the repository source and the installed-package inspection artifacts.

## Base differentiator contract

### `tfq.differentiators.Differentiator`

- `generate_differentiable_op(*, sampled_op=None, analytic_op=None)`
  - Provide exactly one callable op.
  - `analytic_op` must behave like an expectation op over `programs, symbol_names, symbol_values, pauli_sums` and must not take `num_samples`.
  - `sampled_op` must behave like a sampled expectation op over `programs, symbol_names, symbol_values, pauli_sums, num_samples`.
  - A differentiator can be attached to only one op at a time; call `refresh()` before reusing it.
- `get_gradient_circuits(programs, symbol_names, symbol_values)`
  - Abstract method implemented by gradient-circuit based differentiators.
  - Returns `(batch_programs, new_symbol_names, batch_symbol_values, batch_weights, batch_mapper)`.
- `differentiate_analytic(programs, symbol_names, symbol_values, pauli_sums, forward_pass_vals, grad)`
  - Default implementation uses `get_gradient_circuits` and the attached expectation op.
- `differentiate_sampled(programs, symbol_names, symbol_values, pauli_sums, num_samples, forward_pass_vals, grad)`
  - Default implementation uses `get_gradient_circuits` and the attached expectation op.
- `refresh()`
  - Clears the one-op attachment so the differentiator can be reused.

### Empty-input behavior

- The shared `catch_empty_inputs` path returns `tf.zeros_like(symbol_values)` when `programs`, `symbol_names`, or `symbol_values` are empty.

## Built-in differentiators

| Symbol | Constructor | Main use | Validation / notes |
| --- | --- | --- | --- |
| `tfq.differentiators.ParameterShift` | `ParameterShift()` | General parameter-shift gradients for parameterized circuits. | No arguments. Works with analytic or sampled expectation ops. Internally uses `parameter_shift_util.parse_programs(..., n_shifts=2)` and adds an impurity symbol named `_impurity_for_param_shift`. |
| `tfq.differentiators.ForwardDifference` | `ForwardDifference(error_order=1, grid_spacing=0.001)` | One-sided finite-difference gradients. | `error_order` must be a positive integer; `grid_spacing` must be a positive real number. Inherits from `LinearCombination`. |
| `tfq.differentiators.CentralDifference` | `CentralDifference(error_order=2, grid_spacing=0.001)` | Symmetric finite-difference gradients. | `error_order` must be a positive even integer; `grid_spacing` must be a positive real number. Inherits from `LinearCombination`. |
| `tfq.differentiators.LinearCombination` | `LinearCombination(weights, perturbations)` | Custom finite-difference or user-defined gradient rules. | `weights` and `perturbations` must be lists/tuples/ndarrays of real numbers, same length, at least two entries, and all perturbations must be unique. Zero perturbation is allowed once at most. |
| `tfq.differentiators.Adjoint` | `Adjoint()` | Fast analytic gradients for exact expectation calculation. | Analytic expectation only, with backend `None`. Sampled or noisy backends are rejected. `get_gradient_circuits` is not implemented. |

## Parameter-shift utility

### `tfq.differentiators.parameter_shift_util.parse_programs`

- Signature: `parse_programs(programs, symbol_names, symbol_values, n_symbols, n_shifts=2)`
- Returns:
  - `new_programs`
  - `weights`
  - `shifts`
  - `n_param_gates`
- Purpose: decompose programs, insert the impurity symbol, build shifted program copies, and compute the paired weights/shifts used by `ParameterShift`.
- Default `n_shifts` is `2`.

## Optimizers

| Symbol | Signature | Main use | Result object |
| --- | --- | --- | --- |
| `tfq.optimizers.rotosolve_minimize` | `rotosolve_minimize(expectation_value_function, initial_position, tolerance=1e-05, max_iterations=50, name=None)` | Coordinate-wise minimization for sinusoid-like or linear-combination objectives. | `RotosolveOptimizerResults` |
| `tfq.optimizers.spsa_minimize` | `spsa_minimize(expectation_value_function, initial_position, tolerance=1e-05, max_iterations=200, alpha=0.602, learning_rate=1.0, perturb=1.0, gamma=0.101, blocking=False, allowed_increase=0.5, seed=None, name=None)` | Stochastic gradient-free minimization for noisy objectives. | `SPSAOptimizerResults` |

### Optimizer result fields

- `RotosolveOptimizerResults`: `converged`, `num_iterations`, `num_objective_evaluations`, `position`, `objective_value_prev`, `objective_value`, `tolerance`, `solve_param_i`.
- `SPSAOptimizerResults`: `converged`, `num_iterations`, `num_objective_evaluations`, `position`, `objective_value_prev`, `objective_value`, `tolerance`, `learning_rate`, `alpha`, `perturb`, `gamma`, `blocking`, `allowed_increase`.

### Optimizer input expectations

- `expectation_value_function` should accept a real 1-D tensor of parameters and return a finite real scalar or scalar-like tensor.
- `initial_position` should be a real 1-D tensor or array.
- For Keras-style parameter packing, flatten trainable variables before optimization and restore them inside the objective.
- `spsa_minimize` accepts `seed=` for repeatability.
