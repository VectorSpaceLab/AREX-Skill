# API reference: data, circuits, primitives, connectors, utilities

This reference records the public contracts used by this sub-skill. Prefer
keyword arguments for readability and to avoid relying on positional defaults.
Check the installed package's public API when a release-specific detail is
important.

## Datasets

### `ad_hoc_data`

```python
ad_hoc_data(
    training_size, test_size, n, gap=0, plot_data=False, one_hot=True,
    include_sample_total=False, entanglement="full", sampling_method="grid",
    divisions=0, labelling_method="expectation", class_labels=None,
)
```

Returns four arrays `(x_train, y_train, x_test, y_test)`, or five values with
`include_sample_total=True`. There are `training_size` rows per class in
`x_train` and `test_size` rows per class in `x_test`; each feature row has
length `n`. With `one_hot=True`, labels have two columns. With
`one_hot=False`, labels use `class_labels` (default `[0, 1]`).

Validation and conditional behavior:

- `training_size` and `test_size` must be nonnegative; `n >= 1`.
- `gap >= 0` when `labelling_method="expectation"`.
- `entanglement` is `"linear"`, `"circular"`, or `"full"`.
- `sampling_method` is `"grid"`, `"hypercube"`, or `"sobol"`.
- `divisions` is required for `"hypercube"`.
- `"grid"` is unsupported for `n > 3`; plotting is disabled for `n > 3`.
- `labelling_method` is `"expectation"` or `"measurement"`.
- Plotting additionally requires the package's matplotlib optional dependency.
- Random choices use `algorithm_globals.random`; set
  `qiskit_machine_learning.utils.algorithm_globals.random_seed` before calling
  when reproducibility is required.
- The fifth return value is an array containing the total accepted sample
  count, represented as `[2 * (training_size + test_size)]` by this release.

### `entanglement_concentration_data`

```python
entanglement_concentration_data(
    training_size, test_size, n, *, mode="easy", one_hot=True,
    include_sample_total=False, sampling_method="cardinal",
    class_labels=None, formatting="ndarray",
)
```

This built-in two-class state dataset supports `n` in `{3, 4, 8}`. It applies
pre-trained hardware-efficient ansatz parameters to separable input states.
`mode="easy"` has a larger concentration-of-entanglement separation than
`mode="hard"`. `sampling_method` is `"cardinal"` or `"isotropic"`.

- Default ndarray features have shape `(samples, 2**n, 1)`.
- `formatting="statevector"` returns a Python list of Qiskit `Statevector`
  objects; each state is normalized.
- Labels follow the same one-hot/scalar two-class convention as `ad_hoc_data`.
- `include_sample_total=True` appends an array containing the total generated
  samples.
- Cardinal sampling has only `6**n` unique product-state choices and warns
  when the requested total is large relative to its practical variety; it
  raises when uniqueness cannot be satisfied. Use isotropic sampling for large
  requests.
- The pre-trained model data is shipped with the installed package. Do not
  move or edit it; a model parameter mismatch indicates a broken or mixed
  installation.
- Random choices use `algorithm_globals.random`.

### `phase_of_matter_data`

```python
phase_of_matter_data(
    training_size, test_size, n, *, model="heisenberg", one_hot=True,
    include_sample_total=False, class_labels=None, formatting="ndarray",
    seed=None, backend=None,
)
```

Supported models are `"heisenberg"`, `"haldane"`, `"annni"`, and `"cluster"`.
`n >= 4`; features are normalized ground-state vectors of dimension `2**n`.
The default `backend=None` path builds each Hamiltonian and uses sparse exact
diagonalization. `seed` controls parameter sampling and shuffling, so equal
seeds produce reproducible data. Practical exact diagonalization is limited by
memory and is documented as approximately `n <= 16`; begin much smaller.

The labels and class counts depend on the model:

| model | default phases | class count |
|---|---|---:|
| `heisenberg` | `trivial`, `topological` | 2 |
| `haldane` | `antiferromagnetic`, `paramagnetic`, `spt` | 3 |
| `annni` | `ferromagnetic`, `paramagnetic`, `floating`, `antiphase` | 4 |
| `cluster` | `haldane`, `ferromagnetic`, `antiferromagnetic`, `trivial` | 4 |

`training_size` and `test_size` are total counts, balanced across classes as
evenly as possible (not per-class counts). `one_hot=False` returns strings,
and `class_labels` must have exactly one entry per model phase. The ndarray
format is `(samples, 2**n)` complex; `formatting="statevector"` returns a list
of `Statevector` objects. The fifth result from `include_sample_total=True`
contains the number of states computed for each class.

Passing any non-`None` `backend` activates the VQE approximation path. In this
release the argument is accepted for API consistency, but the implementation
uses Qiskit's `StatevectorEstimator` rather than the supplied backend. VQE may
mislabel points near phase boundaries; use the exact default for reliable
labels.

## Circuit helpers

### `qnn_circuit`

```python
qnn_circuit(num_qubits=None, feature_map=None, ansatz=None)
```

Returns `(composed_circuit, feature_map.parameters, ansatz.parameters)`.
At least one argument is required. If no feature map is supplied, the default
is `z_feature_map` for one qubit and `zz_feature_map` otherwise. If no ansatz
is supplied, the default is `real_amplitudes`. The feature map and ansatz must
agree on qubit count. Supplying `num_qubits` or relying on automatic padding is
deprecated; explicitly construct matching circuits for new code.

### `raw_feature_vector`

```python
raw_feature_vector(feature_dimension)
```

Returns a parameterized initialization circuit with
`log2(feature_dimension)` qubits and one parameter per amplitude. The dimension
must be a positive power of two. Bind all parameters before definition,
transpilation, or statevector evaluation. Bound amplitudes are normalized by
the parameterized instruction when their norm is not already one. This
initialize-based circuit cannot provide gradients for gradient-based circuit
optimizers and is best treated as a data-loading feature circuit.

## Reference primitives

### `QMLEstimator`

```python
QMLEstimator(default_precision=0.0, seed=None, **kwargs)
```

The package's V2-style wrapper around `StatevectorEstimator`.

- `default_precision == 0.0` selects exact mode: analytic expectation values,
  deterministic output, `stds == 0`, and per-call `precision` is accepted but
  ignored.
- A nonzero precision selects delegate mode and forwards execution to the
  Qiskit reference estimator. `seed` may be an integer or NumPy generator.
- `run(pubs, precision=None)` returns a primitive job. PUBs can use the usual
  circuit/observable/parameter-value forms; this implementation additionally
  accepts common observable encodings such as Pauli strings, mappings, and
  `SparsePauliOp`.
- Exact results carry metadata including `exact=True`, `target_precision=0.0`,
  and `shots=None`.

### `QMLSampler`

```python
QMLSampler(shots=None, **kwargs)
```

The package's V2-style wrapper around `StatevectorSampler`.

- `shots=None` selects exact mode. Probabilities are computed analytically and
  deterministically; a per-call `shots` override is accepted for compatibility
  but does not change exact probabilities.
- An integer `shots` selects delegate sampling mode with that default shot
  count; per-call `shots` can override it.
- Exact result data exposes sampler-like `get_probabilities()` and
  `get_counts()` containers. Counts are available without sampling when the
  probability distribution is dyadic; use probabilities for non-dyadic exact
  distributions.
- Circuits should contain final measurements when classical-register data is
  requested. `join_data()` combines register results.

## `TorchConnector`

```python
TorchConnector(neural_network, initial_weights=None, sparse=None)
```

A PyTorch `Module` backed by a Qiskit Machine Learning `NeuralNetwork`.
PyTorch is optional. If omitted, weights are initialized uniformly in `[-1, 1]`;
pass a NumPy array or Torch tensor to make initialization reproducible. The
registered parameter is available as `.weight`, the wrapped network as
`.neural_network`, and the effective sparse setting as `.sparse`.

The input's final dimension must equal `neural_network.num_inputs`. The
connector calls `neural_network.forward` during the forward pass and
`neural_network.backward` during autograd. Set the QNN's `input_gradients=True`
when gradients must continue into an upstream classical Torch layer; weight
training alone can work without input gradients. The output and gradients are
moved back to the input/weight device.

Sparse rules:

- `sparse=True` requires `neural_network.sparse=True` and the `sparse` extra.
- `sparse=True` with a dense QNN fails at construction/forward with a machine
  learning error.
- A dense connector can convert sparse QNN output and gradients to dense
  tensors, but this can use more memory.
- Sparse autograd uses the `sparse` package and Torch sparse COO tensors.

## Utilities

The package exports `algorithm_globals`,
`derive_num_qubits_feature_map_ansatz`, `validate_initial_point`, and
`validate_bounds` from `qiskit_machine_learning.utils`.

- `algorithm_globals.random_seed` is read/write; `.random` is a NumPy
  `Generator`. Setting the package property is the forward-compatible seed
  path.
- `validate_initial_point(point, circuit)` checks parameter length. If `point`
  is `None`, it samples each parameter from circuit bounds, substituting
  `[-2*pi, 2*pi]` when bounds are absent or partially unspecified.
- `validate_bounds(circuit)` returns circuit parameter bounds or
  `(None, None)` for each parameter and rejects a length mismatch.
- `derive_num_qubits_feature_map_ansatz` is the helper used by `qnn_circuit`;
  its `num_qubits` argument and auto-alignment behavior are deprecated.
- `validate_in_set`, `validate_min`, `validate_max`, and range variants live in
  the validation module but are lower-level helpers and are not all re-exported
  from the package root.
- `L1Loss`, `L2Loss`, and `CrossEntropyLoss` live under
  `qiskit_machine_learning.utils.loss_functions`. They validate equal shapes;
  L1/L2 return per-sample values for rank-2+ arrays, and cross entropy clips
  probabilities at `1e-10` before taking `log2`.
- Kernel losses (`SVCLoss`, `SVRLoss`, `MSRLoss`, `MARLoss`, `HuberLoss`) are
  kernel-training utilities. Route kernel-specific use to the kernel skill.
