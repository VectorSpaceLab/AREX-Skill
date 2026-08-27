# QNN and gradient troubleshooting

Use the smallest reproducer first: one or two qubits, one input, one weight,
one observable or two sampler outcomes, and one batch row. Run
`scripts/qnn_smoke.py` to distinguish an installation/import problem from a
circuit or backend problem.

| Symptom | Likely cause | Recovery |
|---|---|---|
| Estimator primitive rejects the circuit | Final measurements are present | Use an unmeasured copy for `EstimatorQNN`; retain measurements only on the sampler copy. |
| Sampler returns no useful distribution or a primitive complains about data | The circuit has no measurement data, or measurements were added too late | Add `measure_all()`/explicit measurements before transpilation, then use the measured circuit in `SamplerQNN`. |
| Runtime/V2 rejects an estimator observable | Observable is still in logical layout while the circuit is ISA/transpiled | Run `isa_observable = observable.apply_layout(isa_circuit.layout)` for every observable and pass the transformed pair. |
| Forward works but backward rejects a runtime circuit | The gradient generated shifted/auxiliary circuits without a compatible pass manager | Supply the same compatible `pass_manager` to the custom gradient (and QNN where applicable), or pre-transpile a fully layout-consistent workflow. |
| Parameter values bind to the wrong gates | Input/weight order was inferred from circuit display or `circuit.parameters` | Pass explicit `input_params` and `weight_params`; verify values are `[all inputs, then all weights]`. |
| `Number of circuit parameters ... mismatch` | A parameter is omitted, duplicated, or included in neither group | Count the circuit parameters and make the two declared groups cover them exactly. |
| `Input data has incorrect shape` | Last input dimension differs from `qnn.num_inputs` | Shape data as `(num_inputs,)` for one sample or `(batch, num_inputs)` for a batch. |
| Output has an unexpected leading dimension | QNN APIs are batch-aware | Treat a one-sample result as `(1, *output_shape)` and compare derivatives using the same batch convention. |
| Input gradient is `None` | `input_gradients` remains false | Recreate or update the QNN with `input_gradients=True`; only do this when the downstream consumer needs input derivatives. |
| Weight gradient is `None` | There are no active weight parameters or no parameter values to differentiate | Declare `weight_params` and provide weights; confirm the circuit has those parameters. |
| Custom sampler interpretation raises an index/shape error | `output_shape` is missing, too small, or has the wrong tuple dimensions | For a mapping into `{0, 1}`, set `output_shape=2`; for a tuple mapping, provide a matching positive tuple. Test every possible mapped index. |
| `output_shape` seems ignored | No custom `interpret` was supplied | With `interpret=None`, output shape is always `2**num_virtual_qubits`; remove `output_shape` or supply an interpretation. |
| A parity model allocates an exponentially large array | Identity interpretation is still active | Use `interpret=lambda x: x.bit_count() % 2` and `output_shape=2`; route sparse concerns to `data-circuits-connectors` when Torch is involved. |
| Sparse QNN construction reports a missing optional dependency | `sparse` is not installed | Install the public extra/package with `python -m pip install sparse`, then rerun import and smoke checks. |
| Sampler register data lookup fails | A dynamic/unexpected classical-register name is exposed by the primitive | Name the register `meas` or `c` and retrieve the primitive's documented data block; avoid relying on arbitrary dynamic attribute names. |
| Finite-shot probabilities or gradients differ between runs | Sampling noise, default shots, or stochastic SPSA | Use shape/probability-sum assertions, increase shots only when justified, and set SPSA `seed`; do not demand exact statevector values from a shot-based primitive. |
| Parameter-shift fails on a gate | The gate is outside that gradient's supported set or has not been decomposed | Decompose/rewrite to supported gates, choose a compatible `LinComb*Gradient`, or use seeded SPSA with an explicitly bounded error tolerance. |
| Direct gradient validation reports length/qubit errors | Circuits, value rows, observables, or selected parameter lists are not aligned | Make all per-circuit sequences the same length; provide one value per circuit parameter and equal-qubit observables. |
| A V1 example no longer imports | V1 primitives are deprecated in current Qiskit | Migrate to public V2 primitives and PUB-style execution; use V1 only when an explicitly supported legacy environment requires it. |
| QFI/QGT has the wrong matrix size | More or fewer parameters were selected than intended | Pass `parameters=[[...]]` explicitly and check the resulting square dimension; start with a one- or two-parameter circuit. |
| QFI/QGT fails on a hardware-style circuit | QGT auxiliary circuits are not ISA-compatible, or the state is not the intended pure state | Use a compatible estimator/pass manager and verify layout for generated observables; QFI/QGT here is for pure parameterized states. |
| Effective dimension rejects samples | Explicit arrays do not have `(N, qnn.num_inputs)` or `(M, qnn.num_weights)` | Inspect `qnn.num_inputs`/`num_weights`; reshape explicit arrays rather than relying on broadcasting. `LocalEffectiveDimension` accepts one vector or `(1, num_weights)`. |
| Effective dimension gives unstable/invalid values | Dataset size is unsuitable for the logarithmic formula or the primitive is noisy | Use positive, sufficiently large dataset sizes, record samples/seed/precision/shots, and compare trends rather than treating one noisy value as a training result. |

## Focused recovery: unapplied observable layout

For a transpiled estimator workflow, preserve the logical observable, run the
pass manager, and transform the observable using the resulting circuit layout:

```python
isa_circuit = pass_manager.run(logical_circuit)
isa_observable = logical_observable.apply_layout(isa_circuit.layout)
qnn = EstimatorQNN(
    circuit=isa_circuit,
    estimator=estimator,
    observables=[isa_observable],
    input_params=input_params,
    weight_params=weight_params,
    gradient=ParamShiftEstimatorGradient(
        estimator=estimator, pass_manager=pass_manager
    ),
)
```

The exact pass manager and primitive must be compatible with the target backend;
this snippet does not claim cloud access or hardware support. If the circuit is
already ISA and the observable is already transformed, do not apply the layout
a second time.

## Focused recovery: sparse parity output shape

A parity map has two valid output indices. Do not use `output_shape=1` or omit
the shape:

```python
qnn = SamplerQNN(
    circuit=measured_circuit,
    sampler=sampler,
    input_params=input_params,
    weight_params=weight_params,
    sparse=True,
    interpret=lambda integer: integer.bit_count() % 2,
    output_shape=2,
)
```

If the mapped function can return a tuple, use a tuple output shape and test
that all tuple components are in range. Install `sparse` before constructing a
sparse network. If a Torch connector is the actual request, route to
`data-circuits-connectors` after confirming this QNN's logical output and
backward shapes.
