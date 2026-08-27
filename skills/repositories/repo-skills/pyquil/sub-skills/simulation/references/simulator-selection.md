# Simulator selection

Read this reference before starting a simulation workflow. It turns the
service boundary and state/noise requirements into an explicit backend choice.
All choices below are for PyQuil 4.18.0 behavior.

## Selection table

| Need | Select | State representation | Service? | Important limit |
|---|---|---|---|---|
| Gate-only, readable local reference | `ReferenceWavefunctionSimulator` | flat `np.ndarray`, shape `(2**n,)` | no | stochastic operations need `rs`; no post-gate noise |
| Gate-only, NumPy tensor implementation | `NumpyWavefunctionSimulator` | tensor `np.ndarray`, shape `(2,)*n` | no | stochastic operations need `rs`; `do_post_gate_noise` is unsupported |
| Quil/QAM-style local execution | `PyQVM(n_qubits, ...)` | delegates to one of the above or density backend | no | `execute` takes a `Program`, resets each call, no batch execution |
| Local post-gate Kraus noise | `PyQVM(..., post_gate_noise_probabilities=...)` | `ReferenceDensitySimulator.density` | no | experimental six-name, single-qubit-after-each-gate model; no density expectation implementation |
| Dense mixed-state state inspection | `ReferenceDensitySimulator` | matrix `(2**n, 2**n)` | no | requires valid Hermitian, trace-one, PSD initial state; O(4^n) |
| QVM wavefunction/expectation/measurement endpoint | `pyquil.api.WavefunctionSimulator` | `pyquil.wavefunction.Wavefunction` or sample array | **yes** | constructs an HTTP QVM client and calls it; not local execution |

## Local decision procedure

1. If the request explicitly says “no service”, “offline”, “in process”, or
   “no QVM”, reject `WavefunctionSimulator` and choose `PyQVM` or a direct
   reference/NumPy simulator.
2. If the caller needs measurements, classical control flow, `Program`
   execution, or several shots, choose `PyQVM`. Supply `seed=...` whenever
   deterministic stochastic behavior matters.
3. If only unitary gates and a flat vector are needed, use
   `ReferenceWavefunctionSimulator(n_qubits, rs=...)`. If a tensor state or
   NumPy contraction behavior is the subject, use
   `NumpyWavefunctionSimulator(n_qubits, rs=...)`.
4. If noise must change a state locally, pass the post-gate probability map to
   `PyQVM`. With no explicit simulator type, PyQVM selects the density backend.
   Keep the map small and explicit, for example
   `{"bit_flip": 0.1}`. It is applied after every gate on every gate qubit.
5. If the requested workflow is a complete channel/readout/noise model,
   experiment grouping, calibration, or `QuantumComputer.run_experiment`,
   stop here and route to `../noise-experiments/` rather than treating the
   PyQVM experimental map as a complete noise model.
6. If the request mentions QVM, a configured endpoint, or compatibility with a
   remote wavefunction service, use `WavefunctionSimulator` only after
   confirming service access. A constructor succeeding proves only client
   creation; `.wavefunction`, `.expectation`, and `.run_and_measure` are the
   service calls.

## Concrete local recipes

### Reference and NumPy state

```python
from pyquil import Program
from pyquil.gates import H, CNOT
from pyquil.simulation import NumpyWavefunctionSimulator, ReferenceWavefunctionSimulator

program = Program(H(0), CNOT(0, 1))
reference = ReferenceWavefunctionSimulator(2).do_program(program)
numpy_sim = NumpyWavefunctionSimulator(2).do_program(program)
vector_from_numpy = numpy_sim.wf.transpose().reshape(-1)
```

`reference.wf` and `vector_from_numpy` are both the canonical vector
`[1/sqrt(2), 0, 0, 1/sqrt(2)]`. The transpose is needed because NumPy stores
q0 on the leftmost tensor axis while the canonical vector names q0 as the
rightmost bit.

### PyQVM state and shots

```python
from pyquil.pyqvm import PyQVM

qam = PyQVM(n_qubits=2, seed=17)
qam.execute(program)
state_tensor = qam.wf_simulator.wf
```

Without a noise map, the default `wf_simulator` is
`NumpyWavefunctionSimulator`. With a noise map and no explicit simulator type,
it is `ReferenceDensitySimulator`. `execute` resets the state for each call;
use `execute_once` only when deliberately preserving state and classical RAM.
`execute_with_memory_map_batch` is explicitly unsupported because PyQVM resets
state per execution.

### Density/noise path

```python
from pyquil.pyqvm import PyQVM

noisy = PyQVM(
    n_qubits=1,
    seed=17,
    post_gate_noise_probabilities={"bit_flip": 0.1},
)
noisy.execute(Program(H(0)))
rho = noisy.wf_simulator.density
```

The supported experimental keys are `relaxation`, `dephasing`,
`depolarizing`, `phase_flip`, `bit_flip`, and `bitphase_flip`. The implementation
applies each selected channel after each gate, independently to each qubit in
that gate. It does not provide distinct 1Q/2Q probabilities or a complete
hardware noise model. Validate `rho.shape`, Hermiticity, trace, and any
observable calculation yourself.

### Service-backed boundary

```python
from pyquil.api import WavefunctionSimulator

service_sim = WavefunctionSimulator(timeout=5.0, random_seed=17)
wavefunction = service_sim.wavefunction(program)  # HTTP QVM request
```

`WavefunctionSimulator` creates a QVM HTTP client from QCS configuration.
Without a reachable QVM, the call raises `api.QVMError`; do not “fix” that by
silently switching the result label to local simulation. Use the bundled Bell
helper for a service-free proof, or route service setup and QVM diagnostics to
`../compile-execute/`.

## Selection record to keep

For reproducibility, record: backend class, `n_qubits`, `seed`/random-state
policy, explicit noise map, whether `execute` or `execute_once` was used,
state representation, and service status. This prevents a remote-QVM result
from being confused with a local PyQVM result.
