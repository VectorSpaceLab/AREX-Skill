# Numerical methods and stochastic equations

Brian2 can choose a state updater automatically, but automatic choice is a
convenience, not a validation result. Inspect the method-choice log and set
`method=` explicitly while debugging or comparing results.

## Available methods

The common `NeuronGroup`, `Synapses`, and `SpatialNeuron` methods are:

- `exact` (also called `linear`) — exact solution of supported linear
  differential systems with constant-over-step coefficients;
- `exponential_euler` — exponential Euler for conditionally linear equations;
- `euler` — forward Euler; for additive stochastic equations this is the
  Euler-Maruyama update;
- `rk2` — midpoint Runge-Kutta;
- `rk4` — classical fourth-order Runge-Kutta;
- `heun` — stochastic Heun for Stratonovich equations with non-diagonal
  multiplicative noise;
- `milstein` — derivative-free Milstein for diagonal multiplicative noise.

GSL methods (`gsl`, `gsl_rkf45`, `gsl_rk2`, `gsl_rk4`, `gsl_rkck`, and
`gsl_rk8pd`) are experimental optional integrations with adaptive internal
steps. They require the appropriate optional GSL support and are not a safe
first recovery target. The network's Brian `dt` still controls scheduling,
monitor resolution, and event/spike timing even when GSL substeps adapt.

## Choosing a method

Classify the equations before choosing:

1. Use `exact` for a genuinely linear system, such as
   `dv/dt = -(v - mu)/tau : 1`, with external values supplied in a namespace.
2. Use `exponential_euler` when the equation is linear in the state but has
   time-varying or state-independent coefficients that make a closed exact
   system inappropriate.
3. Use `euler` for a small deterministic nonlinear fixture or additive noise
   when its time-step error is acceptable. Decrease `dt` and compare outputs.
4. Use `rk2`/`rk4` for deterministic nonlinear equations when accuracy per step
   matters more than the extra function evaluations.
5. Use `heun` or `milstein` only after identifying the stochastic calculus and
   noise structure. A method's name does not repair a dimensionally invalid SDE.

Pass a method name to the owner constructor, for example
`NeuronGroup(..., method="exact")`. A method can reject equations because the
system is nonlinear, a subexpression is not constant over `dt`, a stochastic
term has unsupported structure, or an equation uses a forbidden dependency.
Treat that rejection as useful information: select a compatible updater or
rewrite the model with the intended approximation. Do not disable unit checks or
silence the rejection.

## Noise units and streams

Brian's `xi`/`xi_*` white-noise symbol has units `second**-0.5`. For a
dimensionless state, this additive noise term has the usual shape:

```text
dx/dt = -x/tau + sigma*xi/sqrt(tau) : 1
```

where `sigma` is dimensionless and `tau` is a time. For a state with unit `U`,
the entire right-hand side must have unit `U/second`; keep any coefficient's
unit explicit. Use distinct suffixes for independent streams and reuse one
suffix when the same stream is intended. Brian rejects multiple plain `xi`
terms because their identity would be ambiguous.

Multiplicative noise (`x*xi`, or noise depending on another state) is not
interchangeable with additive noise. Confirm whether the model specifies Ito or
Stratonovich semantics and use a matching updater. Begin with one neuron, a
fixed `dt`, a fixed random seed, and finite-value assertions; only then compare
sample statistics or increase the population.

## Flags that constrain integration

`constant over dt` can make a subexpression eligible for a linear updater and
is mandatory for a stateful function such as `rand()` when it must be sampled
once per step. It changes evaluation semantics, so do not use it as a generic
performance annotation.

`unless refractory` modifies when a `NeuronGroup` differential state updates;
it requires the group to have an actual refractory rule. `event-driven` moves a
linear one-dimensional synaptic equation to event code and cannot be used as a
continuous-neuron shortcut. Event-driven variables cannot feed ordinary
continuous equations.

## A bounded numerical check

For an equation `dv/dt = -v/tau : 1`, initialize `v=1`, use `tau=1*ms`, and
run a small duration with `method="exact"`. Compare the result with
`exp(-duration/tau)`. Repeat with `euler` at two `dt` values and verify that
reducing `dt` reduces the deterministic discretization error. For stochastic
fixtures assert finiteness and structural invariants, not one exact random
trajectory, unless the random seed and target are explicitly part of the test.

Device/compiler failures are outside this reference. First reproduce the
mathematics on the NumPy runtime, then hand target/build questions to the
code-generation route. For errors during method selection, see
[troubleshooting](troubleshooting.md); for equation language and flags, see
[equation syntax](equation-syntax.md).

## Evidence basis

The method names, automatic-selection caveats, stochastic updater assumptions,
and GSL boundary follow the Brian2 2.9.0 user-guide topic **Numerical
integration** and the public state-updater registry exposed through
`NeuronGroup(..., method=...)`, `Synapses(..., method=...)`, and
`SpatialNeuron(..., method=...)`. This route does not claim optional GSL or
compiler support merely because a method name is registered.
