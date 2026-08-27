# Units and equations troubleshooting

Use the smallest explicit `Network` and the NumPy runtime while diagnosing. A
zero-duration run validates more than `Equations(...)` construction, and a
one- or two-step run distinguishes setup failures from numerical failures.
Keep unit checking enabled; the exception usually identifies the offending
object and expression.

## Dimensional failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `DimensionMismatchError` on `a + b`, assignment, or comparison | Addends or assigned values have different dimensions; a bare number was used where a quantity was required | Write the expected dimension beside each term. Use `10*ms`, `-65*mV`, etc.; use `value/unit` or an underscore view only at an intentional unitless boundary. |
| Differential equation reports a mismatch | The unit after `:` was treated as the derivative's unit, or the RHS is missing a per-second factor | Remember `dv/dt : volt` means RHS `volt/second`. Add `/tau`, `/second`, or the correctly dimensioned coefficient. |
| Equation declaration rejects `mV`, `ms`, or `Hz` after `:` | Declarations require base units, not scaled aliases | Declare `volt`, `second`, or `hertz`; assign scaled Python values such as `20*mV`. For concentration use `mmolar`/`mM`, not `molar`, when the intended SI scale is millimolar. |
| A function call fails on units | `@check_units` metadata does not match the input or return value | Make argument metadata complete, use `1` for dimensionless values, return a quantity with `result=...`, and call the function directly once before using it in a model. |
| A result is numerically off by 1e3 or 1e-3 | A base-unit underscore value was confused with a scaled quantity | Check whether the value came from `x_`, `asarray`, or division by a unit. Restore the intended scale explicitly. |

## Parser and identifier failures

- **Unknown identifier at `Network.run`:** list every name not declared as a
  parameter/subexpression or built-in. Put constants and prepared functions in
  the group `namespace` or pass them in `Network.run(namespace=...)`. Then run
  with `namespace={}` to prove no implicit caller variable is being used.
- **Duplicate namespace warning:** the same name exists in a group namespace
  and run namespace (or implicit locals/globals). Keep one authoritative value;
  do not rely on precedence to resolve a model.
- **`np.*`, imports, indexing, or Python syntax fails:** rewrite with Brian's
  bare built-ins (`exp`, `sqrt`, `sin`, `clip`, `int`, and so on). Equation
  strings are translated abstract code, not Python. Move complex control flow
  to a supported `run_regularly`, network operation, or a prepared function.
- **Invalid variable name:** rename identifiers that are Python keywords,
  start with `_`, collide with unit/function/constant names, or equal `t`,
  `dt`, `xi`, `i`, `N`, or another special symbol. Do not invent `xi_*`
  variables; those names are reserved for noise streams.
- **`Equations` parses but group creation/run fails:** this is expected when
  owner-specific unit, namespace, flag, or updater checks have not happened.
  Instantiate the actual owner, call `Network.run(0*second,
  namespace={})`, and fix the first reported issue.
- **Subexpression dependency cycle:** expand the cycle on paper and make one
  direction a parameter or a differential state. Brian cannot topologically
  order mutually dependent definitions.

## Flags and stochastic equations

- **`xi` conflict:** more than one plain `xi` appears in the equation set. Give
  each intended stream a suffix (`xi_exc`, `xi_inh`) and reuse the same suffix
  where correlation is intended. Check that each complete RHS has variable-unit
  per-second dimensions; for a dimensionless state, `sigma*xi/sqrt(tau)` is a
  common shape.
- **`event-driven` rejected:** the flag belongs only on a synaptic differential
  equation and automatic handling is limited to one-dimensional linear forms.
  Remove it or rewrite the synaptic dependency graph; do not use it on a
  neuron equation.
- **`unless refractory` rejected or has no effect:** it belongs on a neuron
  differential equation and requires a refractory rule on the group. Confirm
  the refractory duration/condition and that the state is actually marked.
- **`constant` or `shared` errors:** a constant cannot be changed during a run;
  a shared value is one scalar and shared subexpressions may only use shared
  inputs. Remove the flag for heterogeneous or event-updated values.
- **`constant over dt` changes results:** it freezes a subexpression once per
  time step. Keep it for stateful functions when one sample per step is
  intended, but remove it when within-step reevaluation is part of the model.

## State updater and result failures

- **`exact`/`linear` is not applicable:** the system is not linear in the
  required sense, or a time-varying term is not constant over `dt`. Try
  `exponential_euler` for a conditionally linear form, or an explicit method
  (`euler`, `rk2`, `rk4`) with a documented `dt` check.
- **Stochastic method rejects the equation:** classify additive versus
  multiplicative noise and the Ito/Stratonovich interpretation. Use
  Euler-Maruyama for an additive-noise baseline; use `heun` or `milstein` only
  when its noise assumptions match. Give each noise stream an explicit suffix.
- **NaNs, blow-up, or large oscillations with no exception:** reduce `dt`, check
  time constants and signs, compare a deterministic/no-noise fixture, and
  compare two compatible methods. Automatic method selection can warn rather
  than raise when an unsuitable parameter regime produces unstable values.
- **Event-driven variable is stale or missing:** event-driven variables are
  updated only when their event code executes and are ignored by the continuous
  updater. Check event scheduling and ensure no ordinary equation depends on
  the event-driven variable.
- **GSL option or method is unavailable:** GSL is optional and experimental.
  Reproduce the model with NumPy and a built-in updater first; compiler/library
  installation and standalone issues belong to code-generation or environment
  troubleshooting.

## User-defined function and target failures

1. Call the Python function with correctly unitful and intentionally incorrect
   arguments; confirm the expected `DimensionMismatchError` before simulation.
2. Decorate with `@check_units` or wrap with `Function` and provide every
   argument and return unit. Use `arg_types`/`return_type` for Boolean/integer
   contracts.
3. Use a vector-safe implementation. Brian calls functions over arrays for
   vectorized targets and may pass raw base-unit numbers under a
   `discard_units=True` implementation.
4. Keep the Python/NumPy version working before adding `@implementation('cpp',
   ...)` or `@implementation('cython', ...)`. Supply target dependencies when
   generated code calls another function. A missing target implementation is a
   target capability issue, not a reason to alter equation units.

`discard_units=True` is a common source of false successes: code that refers to
`brian2.mV` or imports units inside the function cannot be safely stripped.
Remove that option or rewrite the implementation in raw base-unit arithmetic.

## Minimal recovery sequence

1. Reduce to one owner and one state variable; set `prefs.codegen.target =
   "numpy"` and use a small explicit `dt`.
2. Write a dimension table for states, derivatives, parameters, namespace
   values, and function arguments/results.
3. Parse the equation, instantiate the owner, and run `0*second` with an
   explicit namespace.
4. Remove flags, noise, and custom functions one at a time; restore each only
   after the base deterministic model passes.
5. Compare `exact`/`euler` or two `dt` values on a bounded fixture; assert
   finiteness and dimensions rather than plotting during triage.
6. Only after the NumPy case is sound, investigate Cython/CPP/GSL or large
   network behavior through the appropriate neighboring route.

For declarations and reserved names, see [equation syntax](equation-syntax.md).
For `Equations`, `Function`, and implementation metadata, see [the API
reference](api-reference.md). For updater assumptions, see [numerical
methods](numerical-methods.md).

## Evidence basis

The failure classes and recovery order are grounded in the Brian2 2.9.0
user-guide topics **Physical units**, **Equations**, **Numerical integration**,
**Namespaces**, and **Functions**, plus the public exception and constructor
contracts exercised by the bundled smoke. This route intentionally stops at
tiny NumPy validation and routes compiler, device, and optional-library
failures to the neighboring code-generation or configuration routes.
