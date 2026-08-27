# QNN construction and execution workflows

These procedures use public package APIs and do not depend on a source checkout.
Use `scripts/qnn_smoke.py` as the smallest executable reference.

## 1. Build a parameter-separated QNN

1. Install `qiskit-machine-learning` and choose a public V2 primitive. Use
   `StatevectorEstimator`/`StatevectorSampler` for a local deterministic-style
   reference check, or the primitive/backend required by the deployment.
2. Build one circuit containing all data and trainable parameters. Keep explicit
   `Parameter` objects or `ParameterVector` entries so they can be passed to
   `input_params` and `weight_params`.
3. Decide the semantic order. Pass `input_params=[...]` first and
   `weight_params=[...]` second. QNN execution binds each row as
   `[inputs..., weights...]`. Verify that the total number of circuit
   parameters equals the two sequence lengths combined.
4. Choose the output contract:
   - expectation outputs: estimator plus one or more observables;
   - probability outputs: sampler plus measurements and optional interpretation.
5. Instantiate the QNN. For a custom gradient, construct it from the same
   primitive and pass it to the QNN. If the primitive needs transpilation, pass
   the appropriate pass manager to both the QNN and the gradient unless using a
   pre-transpiled ISA circuit with already transformed observables.
6. Before fitting or connecting, run one forward and one backward call and
   assert output, input-gradient, and weight-gradient shapes. Full fitting is
   owned by the algorithms route.

## 2. EstimatorQNN local forward/backward

```python
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp
from qiskit_machine_learning.neural_networks import EstimatorQNN

x = Parameter("x")
w = Parameter("w")
circuit = QuantumCircuit(1)
circuit.ry(x, 0)
circuit.rz(w, 0)       # no measurements for EstimatorQNN

qnn = EstimatorQNN(
    circuit=circuit,
    estimator=StatevectorEstimator(),
    observables=SparsePauliOp.from_list([("Z", 1)]),
    input_params=[x],
    weight_params=[w],
    input_gradients=True,
)
output = qnn.forward([0.2], [0.3])
input_grad, weight_grad = qnn.backward([0.2], [0.3])
assert output.shape == (1, 1)
assert input_grad.shape == (1, 1, 1)
assert weight_grad.shape == (1, 1, 1)
```

Multiple observables produce one output column per observable. For batches,
pass an array shaped `(B, num_inputs)` and reuse/broadcast the weight vector.
If input gradients are not needed, leave `input_gradients=False`; then the
first backward return is `None` and only the weight Jacobian is computed.

Do not attach measurements to an estimator circuit for a primitive that rejects
measured circuits. If a circuit was shared with a sampler workflow, make an
unmeasured copy for the estimator path.

## 3. SamplerQNN with identity or parity output

A sampler circuit must expose measurement data. For a custom mapping, provide
its full output shape:

```python
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.primitives import StatevectorSampler
from qiskit_machine_learning.neural_networks import SamplerQNN

x = Parameter("x")
w = Parameter("w")
circuit = QuantumCircuit(1)
circuit.ry(x, 0)
circuit.rz(w, 0)
circuit.measure_all()

parity = lambda measured: measured.bit_count() % 2
qnn = SamplerQNN(
    circuit=circuit,
    sampler=StatevectorSampler(),
    input_params=[x],
    weight_params=[w],
    interpret=parity,
    output_shape=2,
    input_gradients=True,
)
probabilities = qnn.forward(np.array([[0.2], [0.4]]), [0.3])
input_grad, weight_grad = qnn.backward(np.array([[0.2], [0.4]]), [0.3])
assert probabilities.shape == (2, 2)
assert input_grad.shape == (2, 2, 1)
assert weight_grad.shape == (2, 2, 1)
```

Without `interpret`, the output vector has one index per logical bitstring and
scales as `2**num_virtual_qubits`; do not pass a misleading `output_shape` in
that mode. A tuple-returning interpretation requires a matching tuple shape,
for example `(2, 2)`. `sparse=True` changes the array representation, not the
logical shape, and requires installing `sparse`.

For finite-shot samplers, use probability sums and shapes as checks rather than
exact statevector values. Measurement keys can be integer, binary, hexadecimal,
or spaced bit-string forms depending on the primitive; use the QNN's public
postprocessing rather than assuming one spelling in application code.

## 4. Custom gradient and options

1. Construct the primitive.
2. Select `ParamShiftEstimatorGradient` or `ParamShiftSamplerGradient` first.
   Add `options=...` for backend runtime options and `pass_manager=...` when
   gradient-generated circuits must be transpiled.
3. Pass the gradient to the QNN. The QNN calls it only for the parameters that
   are active: all input and weight parameters when `input_gradients=True`, or
   only weight parameters otherwise.
4. For direct gradient use, provide one circuit/observable/value row per job
   entry, then call `.result()` and inspect `result.gradients` plus metadata.
   Use `parameters=[[selected_parameter]]` to request a subset.
5. Use `LinComb*Gradient` when its supported gates and backend behavior are
   appropriate. Use SPSA with positive `epsilon`, bounded `batch_size`, and a
   seed when stochastic finite differences are intentional.

Run-level options override constructor options; constructor options override
primitive defaults. Do not assume an option name accepted by one primitive is
accepted by every vendor or reference primitive.

## 5. V2 transpilation and layout-safe estimator workflow

Use this pattern when an estimator or sampler requires ISA circuits (for
example, a backend-specific V2 primitive):

1. Build the logical parameterized circuit and the logical observable.
2. For sampler circuits, add `measure_all()` or explicit measurements **before**
   the pass manager runs. Prefer classical-register names `meas` or `c`.
3. Run the pass manager to obtain `isa_circuit`.
4. For each estimator observable, compute
   `isa_observable = logical_observable.apply_layout(isa_circuit.layout)`.
5. Construct `EstimatorQNN` with the ISA circuit and `[isa_observable]`, using
   the same estimator. If the chosen gradient will generate additional
   circuits, give its constructor the same pass manager; alternatively use the
   documented QNN/pass-manager route consistently rather than mixing logical
   observables with physical circuits.
6. For sampler, construct `SamplerQNN` with measured ISA circuit and use a
   `ParamShiftSamplerGradient(..., pass_manager=pass_manager)` when needed.
7. Check that the primitive's result data block and classical register names
   are the names expected by the primitive. Run a one-sample forward/backward
   check before batching.

The critical invariant is that every circuit sent to a V2 primitive is in the
backend's accepted instruction set and every estimator observable uses that
circuit's layout. A transpiled circuit plus an original, unapplied observable is
not a valid substitute.

## 6. Effective dimension and local effective dimension

1. Build a working QNN and verify its forward and weight-backward calls first.
2. Choose explicit `input_samples` shaped `(N, qnn.num_inputs)` and
   `weight_samples` shaped `(M, qnn.num_weights)`, or pass bounded integer counts
   for random sampling. Use `algorithm_globals.random_seed` when random samples
   must be repeatable.
3. Construct `EffectiveDimension(qnn, weight_samples=..., input_samples=...)`.
   For a trained/local analysis, use `LocalEffectiveDimension` with one weight
   vector or shape `(1, num_weights)`.
4. Call `get_effective_dimension(dataset_size)` with a positive scalar or array
   of dataset sizes. For diagnosis, call `run_monte_carlo`,
   `get_fisher_information`, and `get_normalized_fisher` separately and inspect
   their shapes.
5. Record QNN type, sample arrays/counts, seed, primitive precision/shots, and
   dataset sizes. The result is a capacity metric, not a training score and not
   evidence that a particular optimizer will converge.
