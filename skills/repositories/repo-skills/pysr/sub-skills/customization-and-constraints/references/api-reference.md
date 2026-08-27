# API reference

## PySRRegressor constructor knobs for this sub-skill

| Parameter(s) | Shape / type | Purpose | Notes |
| --- | --- | --- | --- |
| `binary_operators`, `unary_operators` | `list[str]` | Standard operator lists | Custom operators live here as Julia strings when arity is 1 or 2. |
| `operators` | `dict[int, list[str]]` | Arity-indexed operators | Required for arity 3+. Do not combine with the unary/binary lists for the same operator family. |
| `extra_sympy_mappings` | `dict[str, callable]` | SymPy export mapping | Required for custom operators that must export or reload cleanly. Use SymPy callables. |
| `elementwise_loss` | `str` | Per-sample loss | Accepts a Julia function string or a LossFunctions.jl object. Use 2 args, or 3 with weights. |
| `loss_function` | `str` | Full objective on the raw tree | Signature should behave like `(tree, dataset, options)`. Use for tree traversal and structural penalties. |
| `loss_function_expression` | `str` | Full objective on the expression object | Use for template-style objectives and expression-level manipulation. Signature should behave like `(expression, dataset, options)`. |
| `loss_scale` | `"log"` or `"linear"` | Score scaling | Use `"linear"` when losses may be negative. |
| `constraints` | `dict[str, int \| tuple[int, ...]]` | Per-operator child limits | Tuple length must match operator arity. Power operators usually need a constraint. |
| `nested_constraints` | `dict[str, dict[str, int]]` | Operator nesting limits | Applies during search, not just to final results. |
| `complexity_of_operators` | `dict[str, int \| float]` | Operator complexity costs | Higher values discourage the operator. |
| `complexity_of_constants` | `int \| float` | Constant complexity | Raises or lowers the cost of free constants. |
| `complexity_of_variables` | `int \| float \| list[int \| float]` | Variable complexity | Can be global or per-feature. Per-feature overrides may also be passed to `fit`. |
| `complexity_mapping` | `str` | Custom complexity function | Advanced hook for expression-level complexity logic. |
| `maxsize`, `maxdepth`, `warmup_maxsize_by` | numeric | Hard and staged size control | Leave slack above the target expression size. |
| `parsimony` | float | Extra complexity penalty | Useful when you want a stronger size bias. |
| `dimensional_constraint_penalty` | float | Unit penalty | Soft penalty for dimensional inconsistencies. |
| `dimensionless_constants_only` | bool | Disallow wildcard units on constants | Use when units must stay strict. |
| `mutations`, `default_mutations` | mapping[`AbstractMutation`, float] | Mutation config objects | Preferred over legacy `weight_*` knobs when you want explicit configs. |
| `plugins`, `default_plugins` | sequence[`AbstractPlugin`] | Plugin config objects | Use to combine simulated annealing, adaptive parsimony, or adaptive mutation weights. |
| `precision` | `16`, `32`, or `64` | Floating-point precision | Default is `32`. Custom operators should match the chosen precision. |

## `fit(...)` extras relevant here

```python
fit(self, X, y, *, Xresampled=None, weights=None, variable_names=None, complexity_of_variables=None, X_units=None, y_units=None)
```

| Argument | Purpose | Notes |
| --- | --- | --- |
| `weights` | Per-row or per-output weights | Enables 3-argument `elementwise_loss`. |
| `variable_names` | Column names for `X` | Names must be valid symbols. |
| `complexity_of_variables` | Per-feature costs | Must match the number of input features if provided at fit time. |
| `X_units`, `y_units` | Dimensional annotations | Use DynamicQuantities-style strings. |

## Reload and export helpers that matter for custom operators

| API | Purpose | Notes |
| --- | --- | --- |
| `PySRRegressor.from_file(...)` | Reload a saved run | Supply the same operator definitions and mappings that the saved run needs. |
| `PySRRegressor.sympy(...)` | SymPy export | Requires valid `extra_sympy_mappings` for custom operators. |
| `PySRRegressor.predict(...)` | Numeric evaluation | Uses the selected equation unless an index is provided. |

## Mutation and plugin config classes

### Mutations
| Class | Key fields |
| --- | --- |
| `ConstantMutation` | `perturbation_factor`, `probability_negate` |
| `BacksolveMutation` | `max_library_size`, `lambda_`, `max_iter` |
| `OperatorMutation` | no fields |
| `FeatureMutation` | no fields |
| `SwapOperandsMutation` | no fields |
| `AddNodeMutation` | no fields |
| `InsertNodeMutation` | no fields |
| `DeleteNodeMutation` | no fields |
| `RotateTreeMutation` | no fields |
| `SimplifyMutation` | no fields |
| `RandomizeMutation` | no fields |
| `OptimizeMutation` | no fields |
| `DoNothingMutation` | no fields |

### Plugins
| Class | Key fields |
| --- | --- |
| `SimulatedAnnealingPlugin` | `alpha` |
| `AdaptiveParsimonyPlugin` | `tournament`, `mutation_acceptance` |
| `AdaptiveMutationWeightsPlugin` | `smoothing`, `floor`, `reward` |
| `MutationBurstPlugin` | `retry_attempts`, `compound_probability`, `compound_max_steps` |

## Notes for advanced users
- If you need a custom objective that interprets the tree symbolically, expect `.predict()` and some export helpers to become limited.
- If you only need a simple residual, prefer `elementwise_loss` over a custom full objective.
- If you need a known structural skeleton, route to the structured-expressions sub-skill instead of forcing it with constraints.
