# Constraints and units

## Operator constraints

`constraints` limits how complex each argument of an operator may be.

Example:

```python
constraints={"pow": (-1, 1), "mult": (3, 3), "cos": 5}
```

Meaning:
- `pow`: arbitrary complexity in the base, but only a simple exponent.
- `mult`: each side may be moderately complex.
- `cos`: the argument may have complexity up to 5.

### Rules to remember
- Tuple length must match operator arity.
- Unary operators usually use a single integer.
- Binary operators using `+` or `-` should have equal side constraints.
- Multiplication-style operators may be reordered internally so the more complex side stays on the left.
- Use `operators={3: [...]}` for arity 3+ operators, and supply a matching tuple length.
- Leaving `^` unconstrained usually makes the search explode.

## Nested constraints

`nested_constraints` limits how often one operator may appear inside another.

Example:

```python
nested_constraints={"sin": {"sin": 0, "cos": 0}, "cos": {"cos": 2}}
```

Meaning:
- `sin` may not contain `sin` or `cos` inside it.
- `cos` may nest inside itself up to two levels.
- Any operator not mentioned is treated as unrestricted.

### Important caveats
- Do not rely on `nested_constraints` if the same symbol is used as both unary and binary.
- These limits apply during evolution, not only to the final expression.
- Tight constraints can silently make the target unreachable; leave slack.

## Complexity shaping

Use complexity controls when you want to bias the Pareto front without hard forbidding expressions.

- `complexity_of_operators`: change operator costs.
- `complexity_of_constants`: raise or lower constant cost.
- `complexity_of_variables`: set a global cost or a per-feature list at `fit` time.
- `complexity_mapping`: custom complexity function for rare advanced cases.
- `parsimony`: additional complexity penalty.
- `maxsize`: maximum node count, including operators, constants, and variables.
- `maxdepth`: optional depth cap.
- `warmup_maxsize_by`: grow the allowed size gradually over the run.

### Practical guidance
- If you want a final equation around size 30, set `maxsize` a little above that.
- A 7-feature linear model is already much larger than it looks once all variables and constants are counted.
- `warmup_maxsize_by` is useful when the search jumps to large expressions too early.
- Default parsimony and frequency-based exploration are usually better than hand-tuning first.

## Dimensional constraints

When you know the units of the features and target, enforce dimensional consistency at search time.

```python
model.fit(
    X,
    y,
    X_units=["m", "s"],
    y_units="m / s",
)
```

### Unit rules
- Use DynamicQuantities-style unit strings.
- `"1"` means dimensionless.
- `dimensional_constraint_penalty` is a soft penalty, not a hard ban.
- `dimensionless_constants_only=True` prevents wildcard constants from absorbing units.
- Units currently do not pair well with template-style structured expressions.

### Good habits
- Keep a finite penalty so the search can pass through near-valid expressions.
- Use `precision=64` when unit-bearing values have very large or very small magnitudes.
- Treat units as a search bias and validation tool, not a substitute for domain reasoning.
