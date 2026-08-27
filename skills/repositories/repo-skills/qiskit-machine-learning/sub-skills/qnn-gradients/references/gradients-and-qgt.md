# Gradients, QGT, QFI, and effective-dimension details

## Gradient execution model

A QNN separates circuit parameters into input and weight groups, then calls a
primitive gradient on the concatenated parameter vector. With
`input_gradients=False`, the QNN asks for weight parameters only. With it set to
`True`, it asks for both groups and splits the result back into input and weight
Jacobians. This is why an apparently correct direct gradient can have a
parameter order different from a QNN's returned axes: always compare against
the QNN's declared `input_params` and `weight_params` order.

For estimator gradients, each gradient result is a NumPy vector per submitted
circuit/observable pair. For sampler gradients, each parameter result is a
mapping from measured outcome index to the derivative of that outcome's
probability. `SamplerQNN` applies `interpret` to these indices and aggregates
collisions into the requested output tensor.

The base validation gates are useful diagnostics: equal lengths for circuits,
parameter-value rows, observables (estimator), and parameter selections;
parameterized circuits; one value per circuit parameter; and matching circuit
and observable qubit counts. A selected parameter must belong to its circuit.

## Parameter-shift

`ParamShiftEstimatorGradient` and `ParamShiftSamplerGradient` use analytic
parameter-shift constructions for their supported gates. They support both the
legacy V1 primitive classes in the gradient implementation and V2 primitives,
but new workflows should prefer V2 APIs because V1 is deprecated in modern
Qiskit Machine Learning releases.

The estimator variant accepts `DerivativeType.REAL`, `IMAG`, or `COMPLEX` in
its constructor. The normal expectation-value derivative is real. The sampler
variant returns probability-distribution derivatives and has no observable.
Both accept `options` and `pass_manager`; a per-call option supplied to
`run(..., **options)` overrides the gradient's defaults.

For V2 with a pass manager, parameter-shift transpiles the generated shifted
circuits and applies each estimator observable's layout. The sampler path
keeps the logical-qubit result range based on the transpiled circuit's virtual
qubit count. A backend-specific gradient still needs a pass manager compatible
with the primitive and circuit.

## Linear-combination gradients

`LinCombEstimatorGradient` and `LinCombSamplerGradient` use linear combinations
of unitaries and have a different supported-gate set from parameter-shift.
`LinCombEstimatorGradient` supports real, imaginary, and complex derivative
modes. It generates additional circuits and observables, so V2 use must apply
the pass manager and estimator-observable layout to the generated workload.
Use it only after confirming the circuit decomposes into its supported gates;
unsupported gates are not fixed by increasing shots.

`LinCombSamplerGradient` works on sampler distributions and has no observable.
Its output remains a mapping per differentiated parameter until a
`SamplerQNN` interpretation aggregates it.

## SPSA gradients

`SPSAEstimatorGradient` and `SPSASamplerGradient` estimate all requested
components with simultaneous random perturbations. Their verified constructors
include `epsilon=1e-6`, `batch_size=1`, and optional `seed`. `epsilon` must be
positive. Increase `batch_size` for a less noisy estimate at greater primitive
cost; keep it bounded for a smoke or interactive diagnosis. A seed makes the
perturbation vectors reproducible, but finite-shot primitive noise can still
vary results.

SPSA is an estimator/sampler gradient implementation, not the optimizer itself.
If the request is to select or run SPSA/QNSPSA training, route the optimizer
portion to `algorithms` or `optimizers` as appropriate.

## Options, precision, and pass managers

There are three option levels for gradient execution:

1. options passed to `run`,
2. options supplied when constructing the gradient,
3. the primitive's defaults.

Higher levels override lower levels. `EstimatorQNN.default_precision` is the
forward estimator precision default; QGT and QFI expose their own precision
flow. `QFI( qgt, precision=...)` overrides the QGT precision for its run unless
an explicit `precision` is supplied to `QFI.run`.

A pass manager is not just an optimization hint for a backend that accepts only
ISA circuits. Gradient implementations create shifted or auxiliary circuits;
if those generated circuits are not transpiled, a runtime primitive may reject
them. Pass the same compatible pass manager to the QNN's gradient, or use a
pre-transpiled circuit and transform all estimator observables with
`apply_layout`. Do not transform the circuit while leaving observables in the
logical layout.

## QGT and QFI

`LinCombQGT` computes the quantum geometric tensor for a pure parameterized
state. Its matrix dimension is the number of selected parameters. With
`phase_fix=True` it subtracts the phase-fix outer-product term; with
`DerivativeType.COMPLEX` it returns complex QGT entries, while real or
imaginary modes return the corresponding component. `run` accepts one or more
circuits, parameter rows, an optional selected-parameter list per circuit, and
scalar or per-circuit precision.

`QFI` wraps a `BaseQGT` such as `LinCombQGT`. It temporarily requests the real
QGT derivative and returns QFI matrices `4 * qgt.real`. Use it for pure-state
Fisher geometry, not as a replacement for an arbitrary classical loss Hessian.
Call `result = qfi.run(...).result()` and inspect `result.qfis`, `metadata`, and
`precision`.

The QGT/LCU path may generate a large triangular set of auxiliary circuits for
many parameters. Start with one circuit and a small selected parameter list;
record precision, phase-fix, derivative type, and pass-manager settings.

## Effective dimension

`EffectiveDimension` runs QNN forward and weight-backward calls over input and
weight samples. Internally it converts estimator outputs/gradients to the
probability-style two-outcome representation before Fisher calculations. The
main intermediate contracts are:

- `run_monte_carlo()` returns gradients shaped
  `(N*M, output_size, num_weights)` and outputs `(N*M, output_size)`;
- `get_fisher_information(gradients, model_outputs)` returns
  `(N*M, num_weights, num_weights)`;
- `get_normalized_fisher(...)` returns an averaged normalized matrix per weight
  sample plus its trace;
- `get_effective_dimension(dataset_size)` returns one scalar or an array of
  values for the requested dataset sizes.

Explicit arrays must have exactly the QNN input/weight dimensions. Integer
counts generate random samples through QML's `algorithm_globals`. Use
`LocalEffectiveDimension` when the analysis must use exactly one weight set.
Zero-probability outputs are clipped/masked in the Fisher calculation, but
invalid sample shapes and unsuitable dataset sizes remain caller errors.
