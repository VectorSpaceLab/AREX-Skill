# Workflows

## Pick the layer first

- **Append or prepend a fixed circuit**: `AddCircuit`.
- **Measure expectation values**: `Expectation` for analytic/noisy readout,
  `SampledExpectation` for sampled expectation values.
- **Draw bitstring samples**: `Sample`.
- **Inspect raw states or unitaries**: `State` or `Unitary`.
- **Train a quantum model with managed symbols**: `PQC`.
- **Train a quantum model driven by classical features**: `ControlledPQC`.
- **Train a noisy quantum model**: `NoisyPQC` or `NoisyControlledPQC`.

## Workflow 1: wire a tiny hybrid model

Use this pattern when the user wants a safe, repeatable model-wiring check.
It is the smallest useful shape for this sub-skill because it combines circuit
batching, `AddCircuit`, and a trainable readout.

```python
circuits = tfq.convert_to_tensor([circuit_a, circuit_b])
helper = cirq.Circuit(cirq.X(qubit))
readout = cirq.Z(qubit)

circuit_in = tf.keras.Input(shape=(), dtype=tf.string)
augmented = tfq.layers.AddCircuit()(circuit_in, append=helper)
outputs = tfq.layers.PQC(model_circuit, readout)(augmented)
model = tf.keras.Model(circuit_in, outputs)

# The batch size should stay at 2 and the outputs should be finite.
```

Recovery checks for this pattern:

1. Confirm the input tensor has batch size 2.
2. Confirm the `PQC` output shape is `[2, n_operators]`.
3. Confirm the output is finite before trying a larger training loop.

## Workflow 2: choose analytic versus sampled readout

- Start with `Expectation` when the circuit and operators can be evaluated
  analytically.
- Switch to `SampledExpectation` when you need shot-based estimates but still
  want the same high-level Keras readout interface.
- Use `Sample` when you need the raw samples instead of expectation values.
- If the user says "I need a noisy readout", check whether the layer should be
  `Expectation(..., backend='noisy')`, `SampledExpectation(..., backend='noisy')`,
  or one of the noisy PQC variants.

Recommended wiring rules:

- `Expectation` and `SampledExpectation` can manage `symbol_values` for you if
  you omit them.
- In noisy or sampled mode, always provide a positive `repetitions` value.
- If a custom backend object is involved, verify the accepted class before
  wiring it in.

## Workflow 3: train a PQC from quantum data

Use `PQC` when the model circuit has trainable symbols and the inputs are
quantum data circuits.

1. Build a `cirq.Circuit` with the symbols you want to train.
2. Pick one or more readout operators.
3. Choose analytic mode with `repetitions=None`, or sampled mode with a
   positive `repetitions` count.
4. Feed circuit tensors through a compiled `tf.keras.Model` if the data source
   is dynamic.

Small-model pattern:

```python
quantum_in = tf.keras.Input(shape=(), dtype=tf.string)
out = tfq.layers.PQC(model_circuit, operators, repetitions=None)(quantum_in)
model = tf.keras.Model(quantum_in, out)
```

## Workflow 4: add classical control inputs

Use `ControlledPQC` when the circuit should be driven by classical features or
another neural-network branch.

1. Keep the quantum data batch free of symbols.
2. Build the classical branch so its last dense layer has one column per model
   symbol.
3. Call the layer with `[quantum_data, control_values]`.
4. Make sure the control tensor column order matches `layer.symbols`.

This pattern also appears in `quantum_reinforcement_learning`-style wiring,
where a circuit is paired with a classical policy network.

## Workflow 5: switch to noisy training

Use the noisy variants when the model circuit already contains noise and the
noisy behavior is part of the training target.

- `NoisyPQC` is the noisy replacement for `PQC`.
- `NoisyControlledPQC` is the noisy replacement for `ControlledPQC`.
- Both require `repetitions` and an explicit `sample_based` boolean.
- Both reject custom backend objects; if the user needs a custom backend,
  choose the non-noisy family instead.

Suggested recovery path for a noisy-model prompt:

1. Add a positive `repetitions` count.
2. Set `sample_based` explicitly to `True` or `False`.
3. Verify whether the model should be a noisy PQC or a non-noisy PQC with a
   custom backend.

## Workflow 6: inspect state or unitary for debugging

Use `State` and `Unitary` for tiny-circuit inspection and model debugging.

- `State` is for final state vectors or density matrices.
- `Unitary` is for exact circuit unitary inspection.
- These layers are most useful on tiny circuits because their outputs are
  ragged and large quickly.

## Notebook anchors

These notebook names are useful as evidence anchors when shaping prompts:

| Notebook anchor | Layer pattern it demonstrates |
|---|---|
| `hello_many_worlds` | `Expectation`, `ControlledPQC`, `AddCircuit` |
| `gradients` | `Expectation`, `SampledExpectation`, differentiator attachment |
| `noise` | `Sample`, `SampledExpectation`, `Expectation`, `PQC`, `NoisyPQC` |
| `qcnn` | `AddCircuit` + `PQC` |
| `mnist` | `PQC` |
| `quantum_reinforcement_learning` | `ControlledPQC` |
| `research_tools` | `Sample`, `State` |

## Shared smoke and notebook note

- From the root `tensorflow-quantum` skill directory, use the shared smoke helper
  `python scripts/tfq_smoke_check.py --quick --layers` for a quick import plus
  tiny layer sanity check.
- The bundled notebook-derived recipes are the runtime guidance for this
  workflow; whole-notebook execution is maintainer-only and not the default
  path here.
