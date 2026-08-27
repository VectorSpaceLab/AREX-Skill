# Modeling Basics Troubleshooting

## Purpose

Read this when a small Pyomo model fails before any data loading, CLI work, or
structured transformation is involved.

## Common failures

### Domain or bound warnings on assignment

Symptoms:

- `W1001` or `W1002` warnings.
- A value is accepted but does not look like the intended domain.

Likely causes:

- Assigning a value outside the declared domain or bounds.
- Using the wrong Pyomo type for the value you want to store.

Recovery:

- Re-check the domain and bounds on the variable.
- Use a smaller example and print the value with `value()`.

### `RecursionError` or deep expression-tree warnings

Symptoms:

- A deep expression tree triggers recursive-walker warnings.

Likely causes:

- Very deep nested expressions.
- Callbacks that recurse through the expression tree.

Recovery:

- Simplify the expression structure.
- Use the nonrecursive walker path when available.

### `None` or missing values during evaluation

Symptoms:

- `value()` fails or prints `None` for a component you expected to be set.

Likely causes:

- The component was not initialized.
- The model is still abstract or incomplete.

Recovery:

- Inspect the component declaration and initialization.
- Confirm that you are using `ConcreteModel` when you expect immediate
  construction.

## Next step

If the issue is actually data loading, solver execution, or a specialized model
family, move to the matching sub-skill instead of debugging it here.
