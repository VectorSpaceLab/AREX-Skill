# Troubleshooting data, circuits, primitives, and connectors

Use the smallest failing example first. Run the bundled probes from an
arbitrary working directory; they do not depend on the current directory:

```bash
python /path/to/skill/scripts/check_install.py
python /path/to/skill/scripts/dataset_smoke.py
python /path/to/skill/scripts/torch_connector_smoke.py
```

Install public packages with `pip install qiskit-machine-learning` and add
`'qiskit-machine-learning[torch]'` or `'qiskit-machine-learning[sparse]'` for
optional integrations. CUDA Torch itself should be installed using the
PyTorch installation selector for the target platform.

## Import and optional dependency failures

### `ModuleNotFoundError: qiskit` or `qiskit_machine_learning`

The base package or its Qiskit dependency is not available in the active
interpreter. Check the interpreter used by the command:

```bash
python -c "import sys; print(sys.executable)"
python -m pip show qiskit-machine-learning qiskit
```

Install into that same interpreter, then rerun `check_install.py`. Do not
repair the issue by adding a checkout path to `PYTHONPATH` in a Researcher
workflow; use a public package installation.

### `MissingOptionalLibraryError` for PyTorch

`TorchConnector` is guarded by the PyTorch optional contract. Install:

```bash
python -m pip install 'qiskit-machine-learning[torch]'
```

Then verify `import torch` and rerun the CPU connector smoke. The package can
still be used for datasets, circuits, primitives, and non-Torch QNNs without
PyTorch.

### Sparse import failure

Sparse connector mode needs both a sparse-capable QNN and the `sparse` package:

```bash
python -m pip install 'qiskit-machine-learning[torch,sparse]'
```

The `sparse` extra is not a replacement for `torch`; install both when using
Torch sparse COO output. If only a dense result is needed, set `sparse=False`
and avoid the extra.

## Dataset shape and reproducibility failures

### Wrong number of rows

Remember that `ad_hoc_data` and entanglement concentration sizes are **per
class**. `ad_hoc_data(training_size=2, test_size=1, ...)` returns four training
rows and two test rows. Phase-of-matter sizes are total rows and are balanced
across the model's classes.

### Wrong tuple unpacking

The default is four values. Add a fifth variable only when
`include_sample_total=True`:

```python
x_train, y_train, x_test, y_test = dataset(...)
x_train, y_train, x_test, y_test, totals = dataset(
    ..., include_sample_total=True
)
```

### Repeated calls differ despite a seed

Use the seed mechanism belonging to the dataset. `ad_hoc_data` and
entanglement concentration read `algorithm_globals.random_seed`; phase of
matter takes `seed=`. If Torch initialization or a data loader is involved,
also set `torch.manual_seed`. Record all seeds and call order: a shared global
RNG advances between calls.

### `ad_hoc_data` rejects the sampling configuration

- `sampling_method="grid"` requires `n <= 3`.
- `sampling_method="hypercube"` requires a nonzero `divisions` value.
- `entanglement` must be `linear`, `circular`, or `full`.
- `labelling_method` must be `expectation` or `measurement`; a negative gap is
  rejected for expectation labels.

For a quick higher-dimensional fixture, use `sampling_method="sobol"` and
set `plot_data=False`.

### Entanglement concentration is slow or rejects a request

Cardinal sampling draws from a finite set of six single-qubit axes. It warns as
requests approach the practical unique-state pool and raises when no unique
choices remain. Use `sampling_method="isotropic"`, reduce sample counts, or
use `n=3` for a smoke. Only `n=3`, `4`, and `8` are supported.

### Phase-of-matter generation is slow or memory-heavy

Exact ground-state computation scales with the `2**n` matrix dimension. Start
with `n=4` and small train/test sizes. Do not pass a non-`None` `backend` to
speed up or improve labels: this release switches to an approximate VQE path,
and its backend argument is currently reserved rather than used to execute on
the supplied backend. Use exact mode for reliable phase labels.

## Qubit, parameter, and raw feature failures

### `qnn_circuit` cannot derive a configuration

At least one of `num_qubits`, `feature_map`, or `ansatz` is required. If two
circuits are provided, their `.num_qubits` values must match. Construct
matching feature map and ansatz circuits explicitly; automatic padding and the
`num_qubits` argument are deprecated and may be removed.

### Dataset input dimension does not match QNN

Inspect both sides:

```python
print(x_train.shape)
print(qnn.num_inputs, qnn.num_weights, qnn.output_shape)
```

The connector requires `input_tensor.shape[-1] == qnn.num_inputs`. A row from
`ad_hoc_data(..., n=4)` has four scalar inputs. A statevector from an `n=4`
dataset has 16 amplitudes and is not a four-input classical row. Choose a
state-preparation circuit or a feature preprocessing step deliberately.

### `raw_feature_vector` rejects the dimension

`feature_dimension` must be an exact positive power of two. The number of
qubits is `log2(feature_dimension)`. Bind every amplitude before transpiling or
calling `decompose`; the placeholder instruction intentionally cannot define
itself while parameters remain unbound. Normalize complex amplitudes as part
of the data contract even though the bound instruction normalizes as needed.

### Gradient cannot be computed through raw feature loading

`raw_feature_vector` is built on `initialize`, which is not a gradient-based
feature map. Use a differentiable feature map, or keep raw loading outside the
parameterized optimization path.

## Primitive result failures

### Exact estimator values differ from a sampled reference

This is expected when comparing `QMLEstimator()` with a finite-precision
`StatevectorEstimator`. Exact mode returns analytic values and zero standard
deviation. To compare delegate behavior, use the same nonzero precision and
seed in `QMLEstimator(default_precision=...)` and the reference primitive.

### Exact sampler has no usable counts

`QMLSampler()` returns probabilities exactly. `get_counts()` can synthesize
counts only for dyadic probabilities. Use `get_probabilities()` for values such
as irrational rotation probabilities, or construct `QMLSampler(shots=...)` when
actual sampling is required.

### Sampler output/register ordering is surprising

Use final measurements and inspect classical-register names. For multiple
registers call `join_data([name1, name2])` explicitly. Qiskit's little-endian
bit convention means textual bitstrings and qubit indices may appear reversed
relative to a diagram; compare against `Statevector.probabilities_dict` with
explicit `qargs`.

## Torch forward/backward and device failures

### Connector construction rejects sparse mode

`TorchConnector(sparse=True)` requires `neural_network.sparse=True`. The
connector flag does not sparsify a dense QNN. Set `sparse=False`, or construct
a QNN that natively returns sparse arrays and install the sparse extra.

### Forward raises invalid input dimension

The connector checks only the final dimension, so a batch is fine but the last
axis must equal `neural_network.num_inputs`. Remove accidental label columns,
flatten only the intended batch axes, and do not pass a statevector amplitude
axis to a QNN designed for coordinate features.

### Output/gradient is detached or upstream layer has no gradient

Construct the QNN with `input_gradients=True` before wrapping it. Confirm
`input_data.requires_grad` and that the loss depends on the connector output.
The connector itself computes weight gradients through the QNN's
`backward`; upstream classical layers need input gradients from the QNN.

### Torch dtype or device mismatch

The connector converts QNN NumPy results to Torch floating tensors. Start with
`torch.float32` inputs, keep the connector and input on the same device, and
move the result explicitly if combining with another device-specific layer.
For CUDA, check `torch.cuda.is_available()` before creating a CUDA tensor. If
false, run the CPU path rather than forcing a device string. CUDA availability
is independent of Qiskit and Qiskit Machine Learning import success.

### Sparse output breaks a downstream Torch layer

Sparse COO tensors support fewer operations. Call `.to_dense()` at the
boundary only when the resulting memory use is acceptable, or keep subsequent
layers sparse-aware. A dense connector (`sparse=False`) can materialize a
sparse QNN result without changing the QNN itself.

### Autograd fails on a high-rank batch

The connector contracts Jacobians with an Einstein-summation signature using
lowercase letters and supports at most 25 dimensions in that helper. Flatten
spatial/batch dimensions while preserving the final input axis, or process a
smaller batch.

## Save/load failures

Save a hybrid model's `state_dict`, not an opaque connector instance, and
recreate the same QNN/circuit before loading:

```python
torch.save(model.state_dict(), "model.pt")
new_model = build_same_model()
new_model.load_state_dict(torch.load("model.pt"))
```

A changed circuit parameter ordering, output shape, sparse setting, or weight
count is a model-compatibility change and must be resolved before loading.
