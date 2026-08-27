# V2 Primitives and Sharp Bits

Use this reference whenever a task mixes Qiskit Machine Learning 1.0.0 with
V2 primitives, IBM Runtime, a pass manager, or a transpiled circuit.

## Primitive migration

Qiskit Machine Learning 0.8+ supports Qiskit V2 primitives while retaining
some V1 compatibility during migration. Prefer `StatevectorEstimator` or
`StatevectorSampler` for local deterministic checks and pass an explicit
primitive to `EstimatorQNN`, `SamplerQNN`, `VQR`, `VQC`, `ComputeUncompute`, or
a kernel when the default is not appropriate. V1 APIs are deprecated and
should not be introduced into new code.

The package's own `QMLEstimator` and `QMLSampler` can provide exact/reference
behavior for local checks. An estimator circuit must not contain classical
measurement instructions; a sampler circuit needs measurements or a compatible
sampler data layout.

## Transpilation and layouts

1. Build the parameterized circuit with the intended measurements when it will
   be sampled.
2. Create a pass manager for the actual backend and run it on the circuit.
3. If an estimator observable is attached to a transpiled circuit, transform it
   with the circuit layout before constructing `EstimatorQNN` or submitting the
   PUB. Do not reuse an observable written for the pre-transpile qubit order.
4. If a gradient implementation creates derivative circuits and the primitive
   requires ISA circuits, give the same compatible pass manager to the gradient
   object as well as to the QNN when applicable.
5. Preserve parameter order explicitly with `input_params` and `weight_params`;
   do not rely on a visually inferred order after circuit composition.

The core pattern is:

```python
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

pass_manager = generate_preset_pass_manager(
    optimization_level=0, backend=backend
)
isa_circuit = pass_manager.run(circuit)
isa_observable = observable.apply_layout(isa_circuit.layout)
```

Then pass `isa_circuit` and `isa_observable` to the QNN or estimator workflow.
For a sampler, add `qc.measure_all()` before transpilation and read the named
result data block (`meas` or `c`) rather than depending on an arbitrary dynamic
classical-register name.

## Common migration errors

- **Estimator rejects measurements:** remove measurements from the estimator
  circuit; use a sampler workflow when counts are required.
- **Sampler has no counts or wrong shape:** add measurements before
  transpilation, ensure `interpret` and `output_shape` agree, and inspect the
  result data block name.
- **Observable dimensions/layout are wrong:** apply `isa_circuit.layout` to
  the observable after transpilation.
- **Runtime gradient submission fails:** pass a backend-compatible pass manager
  to the gradient, because parameter-shift/linear-combination methods create
  additional circuits.
- **Noisy gradient looks unstable:** SPSA/LCU-style methods can be noise
  sensitive; reduce the pilot scope, increase controlled shots/resampling, and
  report uncertainty rather than treating one gradient as proof of convergence.

For model-facing recovery, follow the nearest sub-skill's troubleshooting
reference; this document only owns cross-cutting V2 and layout behavior.
