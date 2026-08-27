# Troubleshooting

## 1) `generate_differentiable_op` and signature errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `generate_differentiable_op requires ... sampled_op ... analytic_op ...` | Neither op was provided. | Pass exactly one callable op. |
| `generate_differentiable_op was given both a sampled_op and analytic_op` | Both variants were provided. | Choose the correct branch for the op type. |
| `Provided arguments must be callable` | A non-callable was passed. | Pass the actual TFQ expectation callable. |
| `unexpected signature for analytic_op` or `found num_samples in analytic_op` | A sampled op was attached as `analytic_op`, or the callable still expects `num_samples`. | Use an analytic expectation op without `num_samples`, or move the callable to `sampled_op`. |
| `unexpected signature for sampled_op` | A sampled expectation callable is missing `num_samples` or uses the wrong argument order. | Make sure the callable accepts `programs, symbol_names, symbol_values, pauli_sums, num_samples`. |
| `This differentiator is already used for other op` | The differentiator was attached once already. | Call `refresh()` and reattach it. |

## 2) Adjoint-specific limitations

| Symptom | Meaning | Recovery |
| --- | --- | --- |
| `sample base backends are not supported by the Adjoint method` | You tried to attach `Adjoint` to a sampled op. | Switch to an analytic expectation op, or use another differentiator. |
| `Adjoint differentiator cannot run on a real QPU` / `no accessible gradient circuits` | You called the circuit-circuit path instead of the op-based path. | Use `generate_differentiable_op(analytic_op=...)` and keep the backend `None`. |
| `Adjoint state methods are not supported in sample based settings` | You tried to use `Adjoint` with sampled/noisy expectation calculations. | Use `ParameterShift` or a finite-difference differentiator instead. |

## 3) LinearCombination and finite-difference validation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `weights must be a numpy array, list or tuple` | `weights` is the wrong container type. | Pass a list, tuple, or NumPy array. |
| `Each weight in weights must be a real number` | A weight is complex or otherwise non-real. | Use real coefficients only. |
| `perturbations must be a numpy array, list or tuple` | `perturbations` is the wrong container type. | Pass a list, tuple, or NumPy array. |
| `Each perturbation in perturbations must be a real number` | A perturbation is complex or otherwise non-real. | Use real perturbations only. |
| `weights and perturbations must have the same length` | Coefficients and perturbation lists do not match. | Make both lists the same length. |
| `Must specify at least two perturbations` | A one-point rule was attempted. | Add another perturbation; one point is not enough to differentiate. |
| `All values in perturbations must be unique` | Duplicate perturbation values were supplied. | Remove duplicates; the zero shift can appear at most once. |
| `error_order must be a positive integer` | `ForwardDifference` got a nonpositive or non-integer order. | Use a positive integer `error_order`. |
| `error_order must be a positive, even integer` | `CentralDifference` got an odd, zero, or non-integer order. | Use a positive even integer `error_order`. |
| `grid_spacing must be a positive real number` | Grid spacing was zero, negative, or non-real. | Use a positive real `grid_spacing`. |

## 4) Empty inputs are not failures

- The shared differentiator empty-input path returns `tf.zeros_like(symbol_values)` when `programs`, `symbol_names`, or `symbol_values` are empty.
- This is expected for empty smoke cases and empty batch slices.

## 5) Optimizer convergence and shape issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `rotosolve_minimize` hits `max_iterations` without converging | The objective is not sinusoidal or not suitable for coordinate-wise Rotosolve updates. | Use Rotosolve only on linear-combination / sinusoid-like objectives; otherwise use SPSA or a gradient-based method. |
| `spsa_minimize` behaves erratically or makes little progress | The objective is too noisy, the step sizes are mismatched, or `blocking=True` is too strict. | Tune `learning_rate`, `perturb`, `allowed_increase`, or disable blocking. |
| The optimizer errors on shapes | The objective does not accept a 1-D real parameter vector. | Flatten the parameter vector before calling the optimizer and reshape inside the objective. |
| The objective returns a vector | The optimizer expects scalar-like feedback. | Reduce the output to a scalar before returning it. |
| Repeated runs differ too much | SPSA randomness is uncontrolled. | Set `seed=` for reproducibility. |

## 6) Tiny gradient sanity checks

If the gradients look wrong after the signature checks pass, compare against the one-qubit `Y**alpha` / `X` smoke from `tensorflow_quantum/python/differentiators/parameter_shift_test.py` or the analytic comparisons in `tensorflow_quantum/python/differentiators/gradient_test.py`.
