# QNN and gradient API reference

This reference describes the public `qiskit-machine-learning` 1.0 API shape
used by this route. Install it with `python -m pip install qiskit-machine-learning`
and import only public modules at runtime.

## Base network contract

`NeuralNetwork` is the abstract, stateless interface. Its public calls are:

```python
qnn.forward(input_data, weights)
qnn.backward(input_data, weights)  # (input_grad, weight_grad)
```

The constructor contract is `NeuralNetwork(num_inputs, num_weights, sparse,
output_shape, input_gradients=False)` for subclasses. Useful properties are
`num_inputs`, `num_weights`, `sparse`, `output_shape`, and `input_gradients`;
`input_gradients` can be changed after construction.

Input handling is batch-aware:

- A scalar is accepted for a one-input network and treated as one input value.
- A one-dimensional array/list is one sample and is promoted to a batch.
- The last dimension of an array must equal `num_inputs`.
- Higher-dimensional input arrays are flattened over leading dimensions during
  primitive execution and restored on output.
- `weights` is reshaped to exactly `num_weights` and broadcast across input
  samples. Use `None` when the circuit has no corresponding parameters.

For a batch of size `B`, a QNN with output shape `O` returns `forward` with
shape `(B, *O)` (a single sample retains the leading batch dimension in the
implementation's normal result). `backward` returns input and weight Jacobians
with shapes `(B, *O, num_inputs)` and `(B, *O, num_weights)`. The input Jacobian
is `None` unless `input_gradients=True`; a weight Jacobian can be `None` when
there are no active weight parameters. For an original input shape with two or
more dimensions, leading dimensions are restored around `O` and the derivative
axis.

## EstimatorQNN

The verified constructor signature is:

```python
EstimatorQNN(
    *, circuit, estimator=None, observables=None,
    input_params=None, weight_params=None, gradient=None,
    input_gradients=False, default_precision=0.015625,
    pass_manager=None,
)
```

- `circuit`: parameterized `qiskit.circuit.QuantumCircuit` with no final
  measurements for estimator execution.
- `estimator`: a public V2 estimator such as
  `qiskit.primitives.StatevectorEstimator`; omitted means the QML reference
  estimator is created.
- `observables`: one `BaseOperator` or a sequence. `None` creates the default
  `Z**n` observable. A sequence of `M` observables makes output shape `(M,)`.
  Every observable must match the circuit's logical/target qubit contract.
- `input_params` and `weight_params`: sequences of the circuit's `Parameter`
  objects. Omitted means no values are bound for that category. Their supplied
  order defines the network order, not an accidental visual gate order.
- `gradient`: a `BaseEstimatorGradient`; omitted means
  `ParamShiftEstimatorGradient(estimator=estimator, pass_manager=pass_manager)`.
- `input_gradients`: opt in to derivatives with respect to inputs. This is
  required when a downstream Torch autograd connector needs input derivatives;
  route the connector itself to `data-circuits-connectors`.
- `default_precision`: precision passed to the V2 estimator forward call when
  the QNN executes.
- `pass_manager`: optional object with `run`; use it when the primitive requires
  transpiled/ISA circuits. The corresponding gradient also needs layout-aware
  transpilation, either through its own `pass_manager` or a pre-transpiled
  circuit/observable pair.

The forward output is `(B, M)`. Weight gradients are `(B, M, num_weights)`;
input gradients, when enabled, are `(B, M, num_inputs)`.

## SamplerQNN

The verified constructor signature is:

```python
SamplerQNN(
    *, circuit, sampler=None, input_params=None, weight_params=None,
    sparse=False, interpret=None, output_shape=None, gradient=None,
    input_gradients=False, pass_manager=None,
)
```

- `sampler`: a public V2 sampler such as
  `qiskit.primitives.StatevectorSampler`; omitted means the QML reference
  sampler is created.
- The circuit must produce measurement data. If it has no classical bits,
  `SamplerQNN` adds `measure_all()` to its internal execution copy, but when a
  pass manager is used, add measurements before transpilation so the target
  classical data is correct.
- With `interpret=None`, the identity map is used and output shape is
  `(2**num_virtual_qubits,)`. An explicitly supplied `output_shape` is ignored
  in this mode (a warning is emitted).
- With a custom `interpret`, the callable maps each measured integer to a
  non-negative integer or a tuple of indices. `output_shape` is mandatory and
  must match the mapped index dimensions. For parity classification, use for
  example `interpret=lambda x: x.bit_count() % 2` and `output_shape=2`.
- `sparse=True` requires the public `sparse` package. The forward and backward
  results are sparse arrays (COO after postprocessing) with the same logical
  shapes as dense results.
- `gradient`, `input_gradients`, and `pass_manager` have the same role as in
  `EstimatorQNN`, using sampler-specific gradient implementations.

With output shape `O`, forward is `(B, *O)`, weight gradients are
`(B, *O, num_weights)`, and input gradients are `(B, *O, num_inputs)` when
requested. Probabilities are aggregated after `interpret`; they should sum to
approximately one per sample, subject to finite shots.

## Gradient classes

All gradient `run` calls return an asynchronous job; call `.result()` to get a
result dataclass. The base estimator gradient contract is:

```python
gradient.run(
    circuits, observables, parameter_values,
    parameters=None, **options,
)
```

The base sampler gradient contract is:

```python
gradient.run(circuits, parameter_values, parameters=None, **options)
```

`parameters` selects a subset per circuit; `None` means all circuit parameters.
Parameter values must match the circuit parameter count. Estimator gradient
results expose `gradients`, `metadata`, and `options`; sampler gradient results
expose the same fields, with sampler gradients represented as per-parameter
quasi-probability dictionaries.

Verified constructors:

```python
ParamShiftEstimatorGradient(
    estimator, options=None, derivative_type=DerivativeType.REAL,
    pass_manager=None,
)
ParamShiftSamplerGradient(sampler, options=None, pass_manager=None)
LinCombEstimatorGradient(
    estimator, derivative_type=DerivativeType.REAL, options=None,
    pass_manager=None,
)
LinCombSamplerGradient(sampler, options=None, pass_manager=None)
SPSAEstimatorGradient(
    estimator, epsilon=1e-6, batch_size=1, seed=None, options=None,
    pass_manager=None,
)
SPSASamplerGradient(
    sampler, epsilon=1e-6, batch_size=1, seed=None, options=None,
    pass_manager=None,
)
```

Use parameter-shift for the common analytic gate set and small deterministic
checks. Use linear-combination gradients when its supported gates and primitive
requirements fit the circuit. SPSA is stochastic and useful when a finite
parameter-shift/LCU route is unsuitable; use a positive `epsilon`, bound the
`batch_size`, and set `seed` when comparing runs. Estimator `DerivativeType` can
be `REAL`, `IMAG`, or `COMPLEX` where supported; the default real derivative is
the usual expectation-value gradient.

`options` are primitive runtime options. Per-call `run` options take priority
over constructor defaults, which take priority over primitive defaults. A
`pass_manager` belongs on both a custom gradient and the QNN when that gradient
generates/transpiles circuits for a backend that requires ISA input.

## Quantum geometry and effective dimension

```python
LinCombQGT(
    estimator, phase_fix=True,
    derivative_type=DerivativeType.COMPLEX, *, pass_manager=None,
)
QFI(qgt, precision=None)
QFI.run(circuits, parameter_values, parameters=None, *, precision=None)
EffectiveDimension(qnn, weight_samples=1, input_samples=1)
LocalEffectiveDimension(qnn, weight_samples=1, input_samples=1)
```

`LinCombQGT` computes the quantum geometric tensor of a pure parameterized
state. `phase_fix=True` includes the phase-fix term. Its `run` returns QGT
matrices and supports a subset of parameters and scalar or per-circuit
precision. `QFI` wraps a QGT, forces a real derivative during its calculation,
and returns matrices equal to `4 * real(QGT)`.

`EffectiveDimension` accepts integer sample counts (random weight samples from
uniform `[0, 1)` and input samples from a normal distribution) or explicit
arrays shaped `(M, qnn.num_weights)` and `(N, qnn.num_inputs)`. Its
`get_effective_dimension(dataset_size)` performs Monte Carlo forward/backward,
Fisher information, normalization, and effective-dimension calculation.
`LocalEffectiveDimension` enforces one weight set; it accepts a one-dimensional
weight vector or shape `(1, num_weights)`. Keep `dataset_size` positive and
large enough for the logarithmic formula, and record seeds/sample arrays when
reproducibility matters.
