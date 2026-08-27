# Noise model reference

This reference describes PyQuil 4.18.0 behavior. It intentionally separates the
public legacy Kraus API from the newer implementation that is present in the
package but not re-exported as a public `pyquil.noise` API in this release.

## Public legacy Kraus surface

Import the stable surface from `pyquil.noise`:

```python
from pyquil.noise import (
    KrausModel, NoiseModel, add_decoherence_noise, apply_noise_model,
    combine_kraus_maps, correct_bitstring_probs, corrupt_bitstring_probs,
    damping_after_dephasing, damping_kraus_map,
    decoherence_noise_with_asymmetric_ro, dephasing_kraus_map,
    estimate_assignment_probs, estimate_bitstring_probs,
    pauli_kraus_map, tensor_kraus_maps,
)
```

`KrausModel(gate, params, targets, kraus_ops, fidelity)` describes one gate
instance. `params` and `targets` identify the instruction to which the map
applies; `kraus_ops` is a sequence of complex NumPy matrices. Its
`to_dict()`/`from_dict()` representation stores each matrix as a pair of real
and imaginary nested arrays. `NoiseModel(gates, assignment_probs)` stores a
sequence of `KrausModel` objects and a dictionary mapping integer qubit ids to
2-by-2 assignment matrices. `NoiseModel.to_dict()` uses string keys for qubit
ids; `from_dict()` restores integer keys. `gates_by_name(name)` filters the
stored gate models.

A direct `KrausModel` object is metadata; it does not execute a channel. To
attach it to Quil, use a program's noise-definition facilities or
`apply_noise_model`. QVM behavior for `ADD-KRAUS` is stochastic per shot, so an
execution result estimates the channel only after enough samples. A generated
header or transformed program is not an execution result.

## Kraus validation and composition

For an `n`-qubit channel, every `K` must be a square complex array with shape
`(2**n, 2**n)`. A trace-preserving channel obeys

```text
sum(K.conj().T @ K for K in kraus_ops) == identity(2**n).
```

The Kraus representation itself gives complete positivity. The completeness
identity gives trace preservation; neither condition by itself proves that a
hardware device implements the model. Use a numerical tolerance appropriate to
the generated values (the legacy internal validation uses an absolute tolerance
of about `1e-3`). Reject non-square, wrong-dimension, NaN, negative-probability,
or materially non-complete inputs rather than silently reshaping or clipping.

The built-in constructors have these meanings:

| API | Input/output contract |
| --- | --- |
| `pauli_kraus_map(probabilities)` | Accepts exactly 4 probabilities for one qubit or 16 for two qubits, ordered `I,X,Y,Z` or the tensor-product ordering `II,IX,...,ZZ`. Probabilities must sum to one within tolerance. Returns `sqrt(p_i) P_i`. |
| `damping_kraus_map(p=0.10)` | Returns `[diag(1,sqrt(1-p)), [[0,sqrt(p)],[0,0]]]`; `p` is a one-step decay probability. Keep `0 <= p <= 1`. |
| `dephasing_kraus_map(p=0.10)` | Returns `[sqrt(1-p) I, sqrt(p) Z]`; keep `0 <= p <= 1`. |
| `tensor_kraus_maps(k1,k2)` | Returns `[k1_i ⊗ k2_j]`; independent maps on distinct qubits, with tensor order matching the supplied factors. |
| `combine_kraus_maps(k1,k2)` | Returns `[k1_i @ k2_j]`; `k2` is first and `k1` is second on the same subsystem. |
| `append_kraus_to_gate(kraus_ops,U)` | Returns `[K_i @ U]`; the noise follows the ideal gate. |
| `damping_after_dephasing(T1,T2,gate_time)` | Composes dephasing first and damping second using the coherence-time formulas below. |

The tensor ordering matters for multi-qubit basis indices. Preserve the order
used by the target Quil/QVM convention; do not infer that reversing operands is
semantically harmless. Test an asymmetric state or a known basis projector
when operand order matters.

## Coherence-time formulas and gate support

For positive finite `T1`, `T2`, and `gate_time`:

```text
p_damp = 1 - exp(-gate_time / T1)
gamma_phi = gate_time / T2 - gate_time / (2*T1)
p_dephase = (1 - exp(-gamma_phi)) / 2
```

The channel is `combine_kraus_maps(damping, dephasing)`, hence dephasing is
applied first. `T1 = inf` or `T2 = inf` disables that contribution. A physical
model requires `T2 <= 2*T1`; equality means no additional pure dephasing. The
legacy function only explicitly rejects negative times and the `T2 > 2*T1`
case, so callers should reject zero, negative, NaN, and negative gate durations
before calling it. The newer coherence-time constructor rejects non-positive
values explicitly.

`add_decoherence_noise(program, T1=30e-6, T2=30e-6,
gate_time_1q=50e-9, gate_time_2q=150e-9, ro_fidelity=0.95)` is a convenience
builder. It is intended for a native-like set: `I`, `RZ` (left noiseless),
`RX` at the supported fixed angles, and `CZ`. `NO_NOISE` contains `RZ`.
`get_noisy_gate` recognizes `I`, `RX(±pi/2)`, `RX(±pi)`, and `CZ`; an unknown
gate or unsupported parameter raises `NoisyGateUndefined` when the high-level
model is built. A tiny floating perturbation near an allowed RX angle is
matched by the package tolerance, but do not use this to hide an unsupported
parametric gate.

The high-level builder creates a `NoiseModel`, then calls
`apply_noise_model`. It may accept scalar or per-qubit dictionaries for `T1`,
`T2`, and `ro_fidelity`. A dictionary can mention qubits not present in a gate,
which causes corresponding readout definitions to be included. Validate that
all qubits in the experiment have deliberate parameters.

## Asymmetric readout and ISA-derived models

`decoherence_noise_with_asymmetric_ro(isa, p00=0.975, p11=0.911)` accepts the
legacy `CompilerISA` shape and creates default decoherence gate models for the
QVM-supported gates in that ISA. It then uses the same asymmetric assignment
matrix on each model qubit:

```text
A = [[p00, 1 - p11],
     [1 - p00, p11]]
```

This is model construction from an ISA description, not a query of a live
processor and not proof of QVM/QPU execution. Prefer explicit model creation
when per-qubit or per-gate parameters differ. The ISA and topology itself are
owned by `../processor-isa/`.

`apply_noise_model(program, model)` preserves the program's non-instruction
metadata, prepends definitions/pragmas, and replaces recognized gate
applications with named noisy gates. `RZ` and unsupported gates are retained
rather than made noisy by `apply_noise_model`; the high-level decoherence
builder may reject unsupported gates earlier. Calling it again on an already
transformed program can produce duplicate headers or attempt to model noisy
names. Track a boolean/model marker in the caller and apply exactly once.

Inspect transformed Quil for:

- one `DEFGATE NOISY-*` per recognized ideal gate;
- `PRAGMA ADD-KRAUS` entries with the intended target operands;
- `PRAGMA READOUT-POVM` entries with the intended `p00,p01,p10,p11` values;
- original unsupported/noiseless instructions still present;
- no accidental second layer of `ADD-KRAUS` or readout pragmas.

## Readout probability estimation and correction

`estimate_bitstring_probs(results)` expects a two-dimensional `(shots, n_bits)`
array. It returns a tensor of shape `(2,)*n_bits` with entries indexed as
`p[bit_0, bit_1, ...]`, normalized to sum to one. Empty shots are invalid for
estimation. `results` columns define the qubit/readout order; do not sort qubits
independently after collection.

There are two legacy layouts to keep separate. A `READOUT-POVM` pragma and
`estimate_assignment_probs` use the conditional matrix

```text
A[o, t] = p(observed=o | true=t)
A = [[p00, 1-p11],
     [1-p00, p11]]
```

with observed outcomes as rows and prepared states as columns. In contrast,
`NoiseModel.assignment_probs` built by `_decoherence_noise_model` and
`decoherence_noise_with_asymmetric_ro` stores the row-stochastic helper layout

```text
[[p00, 1-p00],
 [1-p11, p11]]
```

The noise-model header passes only its diagonal `p00` and `p11` values to
`Program.define_noisy_readout`, which writes the first conditional layout to
Quil. Do not compare an internal `assignment_probs` array to a flattened
`READOUT-POVM` pragma without this conversion. This distinction is visible in
the 4.18.0 source and tests and is especially important for asymmetric readout;
symmetric matrices hide it.

For independent local readout error, `corrupt_bitstring_probs(p, matrices)`
contracts each tensor axis as `A[i,j]` with the supplied matrix, and
`correct_bitstring_probs` uses the inverse of each matrix and the same axis
order. Supply the layout expected by the transformation you are modeling and
verify a basis-distribution case. Correction is a linear inverse, not a
constrained maximum-likelihood estimator: finite-shot error can produce
negative probabilities or values above one, and an ill-conditioned assignment
matrix amplifies uncertainty. Check shape, finite entries, the relevant row or
column normalization, determinant/condition number, and the corrected tensor's
sum before interpreting it.

`bitstring_probs_to_z_moments(p)` applies the local transform
`[[1,1],[1,-1]]` on each axis. Its index `[j0,j1,...]` selects the moment of
`Z_0**j0 * Z_1**j1 * ...`, where each exponent is 0 or 1. This is a mathematical
post-processing operation and does not run a program.

`estimate_assignment_probs(q, trials, qc, p0=None)` is different: it constructs
and submits two programs (prepare `|0>` and `|1>`, measure `q`) through the
provided `QuantumComputer`. It requires a functioning compiler/QVM/QPU path and
returns the estimated matrix. It must not be used as a service-free smoke test.

## New channel implementation in 4.18.0

The package also contains quax/JAX-backed classes in the implementation modules
`pyquil.noise._channels` and `pyquil.noise._noise_model`. They are **not
re-exported by `pyquil.noise` in 4.18.0** and should be treated as version-pinned,
inspection/migration surfaces rather than assumed stable public API. Do not
pass their `NoiseModel` to the legacy `apply_noise_model`.

The inspected signatures include:

```text
Channel.from_depolarizing_constant(inst, depolarizing_constant, gate_time=1.0, custom_gates=None)
Channel.from_gate_fidelity(inst, fidelity, gate_time=1.0, custom_gates=None)
Channel.from_pauli_fidelity(inst, pauli_fidelity, gate_time=1.0, custom_gates=None)
Channel.from_pauli_generators(inst, pauli_generators, gate_time=1.0, custom_gates=None)
Channel.from_coherence_times(inst, gate_duration, t1s, t2s=None, custom_gates=None)
Channel.from_lindbladian(inst, noise_lindbladian, gate_time=1.0, custom_gates=None)
Channel.from_random_coherent_error(inst, process_fidelity, rng=None, gate_time=1.0, custom_gates=None)
SuperopChannel.from_pauli_noise(inst, pauli_noise, custom_gates=None)
MeasurementChannel.from_readout_fidelity(inst, fidelity, asymmetry=0.0, dim=2)
MeasurementChannel.from_binary_discriminator(inst, dim, threshold, fidelity=1.0)
ResetChannel.from_amplitude_damping(inst, gamma, gate_time=1.0, dim=2)
ResetChannel.from_coherence_times(inst, duration, t1, t2=None)
NoiseModel.from_channels(channels=())
NoiseModel.from_isa(isa)
NoiseModel.from_compiler_isa(compiler_isa)  # deprecated since 4.17.0
```

`Channel` keeps an ideal gate unitary and a Lindbladian process and exposes
fidelity/Pauli-analysis helpers; `MeasurementChannel` models a quantum
instrument; `ResetChannel` is for targeted reset; `CycleChannel` combines
channels on disjoint resources. The newer constructors reject invalid
probabilities/rates, mismatched dimensions, and (for coherence times) non-
positive times or `T2 > 2*T1`. Pauli-flavored analysis is qubit-only; qutrit
channels need a general Lindbladian/superoperator path.

`NoiseModel.from_isa` is the preferred newer ISA entry point when that API is
available. `from_compiler_isa` is deprecated because the rpcq `CompilerISA`
layer is slated for removal in v5. This newer model's `get_channel` lookup and
JSON serialization are useful for model analysis, but 4.18.0 does not make it a
replacement for the public legacy QVM pragma workflow. Verify future-version
migration separately rather than silently changing a user's model family.
