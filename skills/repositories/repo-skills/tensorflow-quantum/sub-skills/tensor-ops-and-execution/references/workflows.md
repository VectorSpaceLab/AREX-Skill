# Workflows

These are the common task shapes for this sub-skill.

## 1) Round-trip a circuit tensor, then run expectation on a resolved symbol

Use this when you need to confirm that TFQ serialization and raw execution are
consistent.

```python
import cirq
import sympy
import tensorflow_quantum as tfq

q = cirq.GridQubit(0, 0)
theta = sympy.Symbol("theta")
circuit = cirq.Circuit(cirq.X(q) ** theta)
serialized = tfq.convert_to_tensor([circuit])
round_tripped = tfq.from_tensor(serialized)
assert round_tripped[0] == circuit

expectation = tfq.get_expectation_op()
observable = tfq.convert_to_tensor([[cirq.Z(q)]])
value = expectation(serialized, ["theta"], [[0.0]], observable)
```

Rules:

- Use `tfq.convert_to_tensor` before execution and `tfq.from_tensor` only when
  you want to inspect or compare Cirq objects.
- Keep `symbol_names` aligned with the columns of `symbol_values`.
- For a zero-angle one-qubit circuit, a `Z` expectation on `|0>` should be
  `+1`.

## 2) Choose the execution backend by output type

Pick the getter first, then choose the backend:

- Expectation values: `tfq.get_expectation_op`
- Sampled expectation values: `tfq.get_sampled_expectation_op`
- Samples: `tfq.get_sampling_op`
- Final states: `tfq.get_state_op`
- Unitary matrices: `tfq.get_unitary_op` / `tfq.core.ops.tfq_unitary_op.get_unitary_op`

Backend rules:

- `backend=None` uses TFQ's native C++ op for that family.
- Expectation backends must behave like `cirq.sim.simulator.SimulatesExpectationValues`
  or `cirq.DensityMatrixSimulator`.
- Sample and sampled-expectation backends must behave like `cirq.Sampler`.
- State backends must behave like `cirq.SimulatesFinalState`.
- A sampler-only backend passed to `get_expectation_op` is the wrong family;
  switch to `get_sampled_expectation_op` instead.

## 3) Resolve symbols, then append circuits before execution

Use this when the final circuit is assembled from separate pieces or when only
some parameters are known.

```python
import cirq
import sympy
import tensorflow_quantum as tfq

q = cirq.GridQubit(0, 0)
programs = tfq.convert_to_tensor([cirq.Circuit(cirq.X(q) ** sympy.Symbol("alpha"))])
values = [[0.25]]
resolved = tfq.resolve_parameters(programs, ["alpha"], values)
joined = tfq.append_circuit(resolved, tfq.convert_to_tensor([cirq.Circuit(cirq.Z(q))]))
```

Rules:

- `resolve_parameters` can resolve only a subset of the circuit symbols.
- `append_circuit` expects both sides to be serialized circuit batches with the
  same batch size.

## 4) Use the noisy path when the circuit has channels

Use the noise namespace when the circuit contains channels or you want Monte
Carlo estimates.

- `tfq.noise.samples` returns noisy bitstrings as ragged tensors.
- `tfq.noise.sampled_expectation` estimates expectations from noisy samples.
- `tfq.noise.expectation` uses the noisy trajectory module to average analytic
  expectations over repeated runs.
- `get_unitary_op` is not the right choice for circuits that contain channels.

## 5) Build commuting exponentials from Pauli objects

Use `tfq.util.exponential` when you need a circuit decomposition for a sum of
commuting Pauli terms.

```python
import cirq
import tensorflow_quantum as tfq

q = cirq.GridQubit(0, 0)
term = 0.5 * cirq.Z(q)
exp_circuit = tfq.util.exponential([term], coefficients=[0.75])
```

Rules:

- Supply only `cirq.PauliSum` or `cirq.PauliString` objects.
- Keep the coefficient list the same length as the operator list.
- Split non-commuting sums before calling `exponential`.

## 6) Handle padded outputs directly only when needed

Most raw execution getters already convert padding to ragged tensors.
Use `tfq.padded_to_ragged` or `tfq.padded_to_ragged2d` only when you are
manipulating raw padded tensors from the op modules yourself.

## 7) Compare circuit similarity with inner product or fidelity

Use the math namespace when you want an overlap or similarity score between a
parameterized circuit batch and a symbol-free reference batch.

```python
import cirq
import sympy
import tensorflow as tf
import tensorflow_quantum as tfq

q = cirq.GridQubit(0, 0)
theta = sympy.Symbol("theta")
programs = tfq.convert_to_tensor([cirq.Circuit(cirq.X(q) ** theta)])
references = tfq.convert_to_tensor([[cirq.Circuit(cirq.X(q))]])
values = tf.convert_to_tensor([[0.0]])
symbols = tf.convert_to_tensor(["theta"])

ip = tfq.math.inner_product(programs, symbols, values, references)
fid = tfq.math.fidelity(programs, symbols, values, references)
```

Rules:

- `other_programs` must be rank 2 and must not contain unresolved symbols; for one comparison circuit use `tfq.convert_to_tensor([[reference_circuit]])`.
- `inner_product` returns complex overlaps; `fidelity` returns squared magnitudes.
- Keep the batch shapes aligned so each circuit row has a matching reference row.

## 8) Use MPS helpers only for 1D circuits

Use the MPS helpers when the task names the 1D MPS simulator explicitly or when
you want a cheaper 1D non-periodic fallback for tiny circuits.

- `mps_1d_expectation` expects 1D non-periodic circuits and a positive bond
  dimension.
- `mps_1d_sample` and `mps_1d_sampled_expectation` follow the same 1D topology
  rule.
- For `mps_1d_sample`, pass a rank-1 sample-count value such as `[3]`; for
  `mps_1d_sampled_expectation`, pass sample counts with the same rank-2 shape as
  the `pauli_sums` tensor, such as `[[10]]` for one circuit and one observable.
- Noise channels are not supported in the MPS helpers.
- If the user asks for general circuits, stay with the raw execution getters
  instead of trying to force MPS.
