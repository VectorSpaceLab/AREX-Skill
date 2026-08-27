# Datasets and circuits: operating guide

## Choose a dataset by feature contract

| Dataset | Feature row | Qubits implied by one row | Labels | Reproducibility |
|---|---|---:|---|---|
| `ad_hoc_data` | real coordinates of length `n` | `n` | two classes, one-hot or custom scalar labels | `algorithm_globals.random_seed` |
| `entanglement_concentration_data` (`ndarray`) | complex amplitudes `(2**n, 1)` | `n` | two classes, one-hot or custom scalar labels | `algorithm_globals.random_seed` |
| `entanglement_concentration_data` (`statevector`) | `Statevector` of dimension `2**n` | `n` | two classes | `algorithm_globals.random_seed` |
| `phase_of_matter_data` (`ndarray`) | complex amplitudes of length `2**n` | `n` | model-dependent phase classes | function `seed` |
| `phase_of_matter_data` (`statevector`) | `Statevector` of dimension `2**n` | `n` | model-dependent phase classes | function `seed` |

Do not feed a statevector feature directly to a circuit with fewer qubits. For
example, a phase-of-matter dataset with `n=4` has 16 amplitudes and needs a
four-qubit amplitude-loading or other state-preparation strategy. Conversely,
`ad_hoc_data(..., n=4)` has four scalar inputs and is naturally paired with a
four-input feature map, not with a four-amplitude raw feature vector.

## `ad_hoc_data`: the fast classification fixture

A compact deterministic starting point is:

```python
from qiskit_machine_learning.datasets import ad_hoc_data
from qiskit_machine_learning.utils import algorithm_globals

algorithm_globals.random_seed = 1376
x_train, y_train, x_test, y_test = ad_hoc_data(
    training_size=20,
    test_size=10,
    n=2,
    gap=0.3,
    one_hot=True,
    sampling_method="grid",
    entanglement="linear",
)
```

The sizes are **per class**, so this produces 40 training rows and 20 test
rows. Each class is placed in its own block in the returned arrays. The
features are generated from the ad-hoc quantum feature-space construction;
`gap` affects expectation-based acceptance/labels. `sampling_method` choices:

- `grid`: uniform grid; only `n <= 3`.
- `hypercube`: stratified variant; set nonzero `divisions`.
- `sobol`: Sobol sequence; useful for dimensions above three or when a grid is
  not suitable.

`entanglement` controls pair terms in the feature-space construction: linear
nearest-neighbor terms, circular terms plus the end-to-end pair, or all pairs.
`labelling_method="expectation"` uses the observable expectation and supports a
nonnegative `gap`; `"measurement"` uses computational-basis measurement. Use
`plot_data=True` only interactively and only when matplotlib is installed.

For custom non-one-hot labels:

```python
x_train, y_train, x_test, y_test = ad_hoc_data(
    4, 2, 2, one_hot=False, class_labels=["negative", "positive"]
)
```

`class_labels` does not change the shape or values of one-hot labels. The
optional fifth result from `include_sample_total=True` is useful when a
sampling method rejects candidate points; preserve it rather than assuming a
hard-coded accepted count.

## Entanglement concentration data

This generator uses bundled pre-trained ansatz weights and supports only
`n=3`, `4`, or `8`. Begin with `n=3`, `mode="easy"`, and cardinal sampling:

```python
from qiskit_machine_learning.datasets import entanglement_concentration_data

x_train, y_train, x_test, y_test = entanglement_concentration_data(
    training_size=2,
    test_size=1,
    n=3,
    mode="easy",
    sampling_method="cardinal",
    formatting="ndarray",
)
assert x_train.shape == (4, 8, 1)
```

The generator returns a two-class dataset: each requested size is per class,
so `training_size=2` yields four training states. `formatting="statevector"`
is usually easier for quantum-information inspection; `formatting="ndarray"`
is convenient for array-based neural-network preprocessing. The two modes
represent a larger (`easy`) or smaller (`hard`) class separation in
concentration of entanglement. `isotropic` sampling avoids the finite cardinal
state pool when more variety is needed.

These are amplitude vectors, not classical feature coordinates. To use them in
a QNN, either preserve the statevector as a prepared input or explicitly
choose an amplitude-loading circuit. Do not flatten a `(2**n, 1)` state into a
length `2**n` vector and then accidentally send it to a QNN expecting `n`
inputs.

## Phase-of-matter data

The phase generator builds a model-specific spin-chain Hamiltonian and computes
ground states. For reliable labels, use exact diagonalization:

```python
from qiskit_machine_learning.datasets import phase_of_matter_data

x_train, y_train, x_test, y_test = phase_of_matter_data(
    training_size=4,
    test_size=2,
    n=4,
    model="heisenberg",
    one_hot=True,
    seed=0,
    backend=None,
)
assert x_train.shape == (4, 16)
```

The requested sizes are total sizes, not per-class sizes. Counts are balanced
as evenly as possible. Models and default phase names:

- `heisenberg`: `trivial`, `topological`.
- `haldane`: `antiferromagnetic`, `paramagnetic`, `spt`.
- `annni`: `ferromagnetic`, `paramagnetic`, `floating`, `antiphase`.
- `cluster`: `haldane`, `ferromagnetic`, `antiferromagnetic`, `trivial`.

Use `one_hot=False` to obtain phase-name strings, or provide a
`class_labels` list with exactly the required number of names. Use
`formatting="statevector"` when quantum-information methods are more useful
than a complex ndarray. `include_sample_total=True` appends per-class totals.

`backend` is a conditional approximation switch, not a reliable hardware
backend injection point in this release: any non-`None` value selects the VQE
path, and the current implementation uses `StatevectorEstimator`
unconditionally. VQE can mislabel points near phase boundaries. Keep
`backend=None` for dataset generation and benchmarking unless the task
explicitly asks for an approximate hardware workflow.

Exact diagonalization cost grows rapidly with `n`; test with `n=4` before
attempting larger chains. A seed stabilizes parameter sampling, class
shuffling, and output ordering. Eigenvectors are phase-canonicalized in the
exact path to improve repeatability.

## Circuit helper workflow

### Compose a QNN circuit

```python
from qiskit_machine_learning.circuit.library import qnn_circuit

circuit, input_params, weight_params = qnn_circuit(num_qubits=2)
```

The helper composes the feature map followed by the ansatz and returns the
parameter views needed by `EstimatorQNN` or `SamplerQNN`. Defaults are
`z_feature_map` for one qubit, `zz_feature_map` for multiple qubits, and
`real_amplitudes` for the ansatz. A safer explicit pattern is:

```python
from qiskit import QuantumCircuit
from qiskit.circuit.library import real_amplitudes, zz_feature_map

feature_map = zz_feature_map(2, reps=1)
ansatz = real_amplitudes(2, reps=1)
circuit, input_params, weight_params = qnn_circuit(
    feature_map=feature_map,
    ansatz=ansatz,
)
```

At least one of `num_qubits`, `feature_map`, or `ansatz` must be present. If
both circuits are supplied, they must have matching qubit counts. The old
`num_qubits` auto-padding behavior emits deprecation warnings and is scheduled
to disappear; avoid using it to repair mismatched circuits.

A difficult but common failure is a dataset/QNN mismatch:

```python
# ad_hoc_data(..., n=4) -> four scalar inputs: use a four-input map
# phase_of_matter_data(..., n=4) -> sixteen amplitudes: use a four-qubit state loader
```

Inspect `qnn.num_inputs`, `qnn.num_weights`, and `qnn.output_shape` before
constructing a connector.

### Load raw amplitude features

```python
from qiskit_machine_learning.circuit.library import raw_feature_vector

raw = raw_feature_vector(8)  # three qubits, eight amplitude parameters
bound = raw.assign_parameters([1, 0, 0, 0, 0, 0, 0, 0])
```

`feature_dimension` must be an exact power of two. The circuit contains a
placeholder parameterized initialize instruction, so transpilation or
`decompose` before all parameters are bound raises a Qiskit error. The bound
instruction normalizes the amplitude vector. Initialization is not a
parameter-shift-friendly feature map; do not expect gradient-based circuit
optimizers to differentiate through it.

## Reproducibility and labels

Use independent, explicit seeds when multiple libraries participate:

```python
from qiskit_machine_learning.utils import algorithm_globals

algorithm_globals.random_seed = 1234  # ad hoc and entanglement datasets
data_seed = 99                         # phase-of-matter seed
```

If a Torch model is randomized, also seed Torch with the same or a deliberately
separate seed. Record dataset arguments, package version, seed source, feature
shape, label encoding, and any fifth `sample_total` output in an experiment
record. Repeating only a model seed does not reproduce a dataset generated from
an unseeded global generator.
