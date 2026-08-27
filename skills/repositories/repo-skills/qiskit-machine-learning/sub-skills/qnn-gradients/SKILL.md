---
name: qnn-gradients
description: "Construct, execute, differentiate, and troubleshoot Qiskit Machine
  Learning neural networks and quantum geometry with EstimatorQNN, SamplerQNN,
  public V2 primitives, and layout-aware gradient workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# QNNs and gradients

Use this route when a request is about `NeuralNetwork`, `EstimatorQNN`,
`SamplerQNN`, `forward`/`backward`, parameter-shift or other QNN gradients,
input gradients, observables, sampler interpretation, sparse outputs, QFI/QGT,
effective dimension, or transpilation/layout handling for these workflows.

## Route and boundaries

- Read [api-reference.md](references/api-reference.md) for public signatures,
  parameter ordering, output shapes, and primitive-version behavior.
- Read [workflows.md](references/workflows.md) for construction, forward/backward,
  custom gradients, layout-aware V2, and effective-dimension procedures.
- Read [gradients-and-qgt.md](references/gradients-and-qgt.md) for gradient
  families, options, derivative types, QGT/QFI, and interpretation of results.
- Read [troubleshooting.md](references/troubleshooting.md) before changing a
  circuit or primitive after an error.
- Run [`scripts/qnn_smoke.py`](scripts/qnn_smoke.py) with `--help` for the
  bundled public-API smoke; run it without arguments for a tiny
  estimator/sampler forward and backward check.

Route full classifier/regressor fitting, optimizers, callbacks, and persistence
to the `algorithms` route. Route fidelity kernels and state-fidelity circuits to
`kernels-fidelity`. Route `TorchConnector`, autograd, sparse Torch integration,
and hybrid PyTorch networks to `data-circuits-connectors`; this route only
supplies the QNN and gradient contract that the connector consumes.

## Operating contract

1. Install the public package in the target environment, for example
   `python -m pip install qiskit-machine-learning`; add `sparse` only for
   sparse `SamplerQNN` output and use the optional dependency required by the
   chosen external primitive/backend when applicable.
2. Decide whether the model output is an expectation value (`EstimatorQNN`) or
   a probability/distribution (`SamplerQNN`). A QNN is stateless: it stores a
   parameterized circuit and primitives, but not trainable weight values or a
   fitting loop.
3. Identify input and weight parameters explicitly. Values are passed to the
   primitive in **inputs followed by weights**, in the exact order of the
   supplied `input_params` and `weight_params` sequences. The circuit must have
   exactly the combined number of parameters.
4. For `EstimatorQNN`, use a circuit without measurements and supply one
   observable or a sequence of observables. For `SamplerQNN`, ensure the circuit
   is measured; custom `interpret` requires an explicit `output_shape`.
5. For a V2/runtime-style primitive that needs ISA circuits, transpile with a
   pass manager and keep its use consistent with the QNN and its gradient.
   Apply a transpiled circuit's layout to each estimator observable. Add sampler
   measurements before transpilation and use stable classical-register names
   such as `meas` or `c`.
6. Check forward and backward shapes against the referenced contract before
   connecting the QNN to another API. Set `input_gradients=True` only when input
   derivatives are needed; the default backward pass returns weight gradients
   and `None` for input gradients.
7. Select a gradient implementation appropriate to the primitive and gates.
   Parameter-shift is the default for QNNs. Pass runtime options at construction
   or at `gradient.run`; run-time options override gradient defaults, which
   override primitive defaults.
8. For QFI/QGT or effective dimension, use an estimator-based QGT on a pure,
   parameterized state, validate sample shapes, and treat shot/precision and
   pass-manager choices as part of the result's reproducibility record.

Do not claim that a CPU reference smoke proves a vendor backend, cloud runtime,
CUDA, or shot-noise behavior. Record an unavailable optional backend as
unverified and preserve the recovery steps in [troubleshooting.md](references/troubleshooting.md).
