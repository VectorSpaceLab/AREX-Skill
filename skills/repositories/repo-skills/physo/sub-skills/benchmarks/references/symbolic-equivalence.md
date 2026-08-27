# Symbolic equivalence checks

PhySO's benchmark comparison is a symbolic convention modeled on SRBench. It
is not a numerical residual test and it does not prove equivalence over every
possible domain.

## Feynman comparison

Use the problem's assumption-aware symbols when parsing a candidate. The
normalized Feynman problem names are usually `x0`, `x1`, ...:

```python
import sympy
import physo.benchmark.FeynmanDataset.FeynmanProblem as Feyn

pb = Feyn.FeynmanProblem(i_eq=18)
trial = sympy.parse_expr(
    "x0*x1/x2", local_dict=pb.sympy_X_symbols_dict
)
is_equivalent, report = pb.compare_expression(
    trial_expr=trial,
    round_decimal=3,
    handle_trigo=True,
    verbose=True,
)
```

`FeynmanProblem.compare_expression` cleans the problem's evaluated target
(`formula_sympy_eval`) and delegates to
`physo.benchmark.utils.symbolic_utils.compare_expression`. For source variable
names, use `original_var_names=True` and parse with
`pb.sympy_original_to_X_symbols_dict`; do not create fresh symbols with the
same printed names but different assumptions.

The target's assumptions come from each variable's declared range. A positive
or negative range receives the corresponding SymPy assumption; a range crossing
zero deliberately does not. Those assumptions affect simplification, so they
are part of the comparison input rather than cosmetic metadata.

## Class comparison

A Class formula contains realization-specific constants. First bind one `K`
row, then compare the candidate for that realization:

```python
import sympy
import physo.benchmark.ClassDataset.ClassProblem as Cls
from physo.benchmark.utils import symbolic_utils as su

pb = Cls.ClassProblem(i_eq=4)  # two K values for this shipped problem
K_vals = [[0.123, 0.456]]
target = pb.get_sympy(K_vals=K_vals)[0]
trial = sympy.parse_expr(
    "exp(-0.345*x0)*cos(0.123*x0 + 0.456)",
    local_dict=pb.sympy_X_symbols_dict,
)
is_equivalent, report = su.compare_expression(
    trial_expr=trial,
    target_expr=target,
    round_decimal=3,
    handle_trigo=True,
)
```

`K_vals` must have one column per `pb.n_spe`. `get_sympy` returns one
expression per row. Compare each realization separately if the candidate has
been evaluated with multiple `K` rows. The `K` symbols are not input variables
and should not be left unevaluated in a candidate intended for one realization.

## What the helper actually tests

`compare_expression(trial_expr, target_expr, ...)` cleans both expressions by
evaluating numeric constants, rounding floats, and simplifying. It then checks:

1. whether the cleaned symbolic difference is zero;
2. whether the difference is a finite constant; or
3. whether the cleaned symbolic ratio is a finite constant.

It runs a vanilla difference/ratio path and, when `handle_trigo=True`, a second
path that rationalizes numbers close to rational multiples of `pi` before
simplifying. The default `round_decimal=2` is the package's SRBench-like
setting; choose a larger value when the candidate's numeric constants warrant
it and record that choice.

The returned report contains `symbolic_error`, `symbolic_fraction`,
`symbolic_error_is_zero`, `symbolic_error_is_constant`,
`symbolic_fraction_is_constant`, `sympy_exception`, and `symbolic_solution`.
`verbose=True` additionally prints the intermediate comparison. Keep the report
for auditability and explain which flag made the Boolean true.

This convention intentionally accepts a constant difference or a constant
ratio. For example, a target `cos(x0)` and trial `cos(x0) + 1` can be reported
equivalent because the difference is constant. Do not use this result as a
strict identity or predictive-accuracy claim; follow it with numerical
validation on generated data when the task needs that stronger guarantee.

## Trigonometric pitfalls

Use symbolic `pi` when expressing a phase identity:

```python
x0 = pb.sympy_X_symbols_dict["x0"]
trial = sympy.parse_expr(
    "exp(-0.345*x0)*sin(pi/2 - 0.123*x0 - 0.456)",
    local_dict=pb.sympy_X_symbols_dict,
)
```

This preserves the exact phase relation `sin(pi/2 - z) == cos(z)`. Passing
`pb.local_dict` instead maps `pi` to a numeric `numpy.pi`; a mathematically
exact identity can then become an approximate floating expression and may fail
at a stricter rounding setting. If source names are used, substitute the
corresponding original-name symbol dictionary while still leaving `pi` symbolic.

`handle_trigo` is limited assistance, not a general trigonometric theorem
prover. It rationalizes floats close to fractions of `pi` (with a bounded
fraction denominator) in the difference or ratio. It cannot repair arbitrary
phase errors, unmatched assumptions, domain singularities, or badly rounded
coefficients. `round_decimal` changes both float cleanup and the tolerance used
for this path; an approximate candidate may pass at one setting and fail at
another.

In particular, a small additive offset can be rounded away, and a constant
remaining difference may still be accepted by the benchmark convention. If
that behavior is not intended, inspect the report and run a numerical residual
check yourself.

## Failure-safe sequence

When a comparison returns `False` or an unexpected `True`:

1. Print `pb.formula_sympy`/`formula_sympy_eval` and the candidate.
2. Check that every variable is parsed through the problem's symbol dictionary.
3. For Class, verify `K_vals` order against `K_names` and substitute all `K`
   symbols before comparison.
4. Retry with a consciously selected `round_decimal` and record
   `handle_trigo`, `prevent_zero_frac`, and `prevent_inf_equivalence`.
5. Inspect the report fields, then evaluate both expressions on a small valid
   sample with `target_function`/`trial_function` if predictive agreement is
   required.

Never infer equivalence from a matching printed string alone. `formula_latex`
is display output, not the parser's source of truth.
