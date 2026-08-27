# Noise and experiment workflows

These workflows are deliberately split into local construction/validation and
backend execution. A successful local step produces an object, matrix, or Quil
string; it does not produce hardware or QVM data.

## 1. Validate a small Kraus model locally

**Inputs:** a gate unitary `U`, a list of Kraus matrices, target qubit count,
and optional readout matrices.

1. Convert every operator with `np.asarray(..., dtype=complex)`.
2. Check shape `(2**n, 2**n)`, finite entries, and
   `sum(K.conj().T @ K) ≈ I`.
3. Check readout matrices are `(2,2)`, finite, nonnegative, and column-stochastic.
4. If composing, preserve order: `combine_kraus_maps(second, first)` means
   `first` then `second` only when named as in the API (`k2` first, `k1`
   second). Write a one-line state-vector/density-matrix check if order is
   consequential.
5. Wrap the map in a `KrausModel` only after the intended gate parameters and
   target order are recorded. Serialize with `to_dict()` if the model crosses a
   process boundary.

**Expected observations:** one-qubit maps are 2-by-2; two-qubit maps are 4-by-4;
completeness is close to identity; a tensor product of two two-element maps has
four operators. If any check fails, stop and fix the model rather than relying
on QVM error messages.

The bundled `scripts/noise_model_smoke.py` performs this workflow with fixed
amplitude damping/dephasing values and a transformed two-qubit program.

## 2. Build decoherence plus asymmetric readout for a tiny ISA

**Inputs:** a version-matched legacy `CompilerISA` or a processor context that
can provide one, `p00`, `p11`, and coherence/gate-time assumptions.

1. Confirm this is the legacy public QVM model path. Do not pass a newer private
   `_noise_model.NoiseModel` to `apply_noise_model`.
2. For a tiny two-qubit ISA, call
   `decoherence_noise_with_asymmetric_ro(isa, p00=0.93, p11=0.82)` or build an
   explicit `NoiseModel` with per-gate Kraus models and per-qubit matrices.
3. Check every gate model's `targets`, `params`, matrix dimension, and
   completeness. Check each assignment matrix is
   `[[0.93, 0.07], [0.18, 0.82]]` for these values.
4. Apply once to a small program such as `RX(pi/2,0); CZ(0,1); RZ(theta,1)`.
   `apply_noise_model` should rename recognized fixed gates to `NOISY-*`, add
   definitions and `ADD-KRAUS` pragmas, add readout pragmas, and preserve
   `RZ(theta,1)` as noiseless.
5. Inspect the transformed Quil. Count headers and verify target operand order.
   Compare the original and transformed program structure; do not execute it.

**Decision point:** if the program contains a gate outside `I`, fixed supported
`RX`, `CZ`, or noiseless `RZ`, either compile/translate it to the supported
native-like set in the compile-execute workflow or choose an explicit custom
model. Do not silently claim that `add_decoherence_noise` modeled it.

**Boundary:** the transformed Quil is ready for a QVM-compatible execution path;
it is not a QVM/QPU observation. A real `estimate_assignment_probs` call also
requires the `QuantumComputer` compiler and QAM services.

## 3. Estimate and correct synthetic readout probabilities

**Inputs:** deterministic shot rows and one assignment matrix per shot column.
No service is needed.

```python
import numpy as np
from pyquil.noise import (
    correct_bitstring_probs, corrupt_bitstring_probs,
    estimate_bitstring_probs, bitstring_probs_to_z_moments,
)

shots = np.array([[0, 0], [0, 1], [1, 1], [0, 0]], dtype=int)
true = estimate_bitstring_probs(shots)
A0 = np.array([[0.90, 0.20], [0.10, 0.80]])
A1 = np.array([[0.95, 0.15], [0.05, 0.85]])
corrupted = corrupt_bitstring_probs(true, [A0, A1])
recovered = correct_bitstring_probs(corrupted, [A0, A1])
moments = bitstring_probs_to_z_moments(recovered)
```

**Validate:** `true.shape == corrupted.shape == (2,2)`, each input tensor sums
to one, and `recovered` is close to `true` for this exact synthetic linear
round trip. With real shot estimates, allow sampling error and do not clip
negative values before reporting the conditioning problem. Confirm that
`A0` corresponds to column 0 and `A1` to column 1; a reversed list is a plausible
but wrong result.

For a real calibration, call `estimate_assignment_probs(q, trials, qc, p0)`
only after the compile-execute owner confirms a functioning backend. It runs
separate `|0>` and `|1>` preparations and returns estimates, not exact matrix
entries.

## 4. Build Pauli settings and verify grouping without execution

**Inputs:** a service-free ansatz `Program`, shot count, preparation states,
and nontrivial Pauli observables.

```python
from pyquil import Program
from pyquil.experiment import Experiment, ExperimentSetting, plusZ, plusX
from pyquil.experiment import group_settings, SymmetrizationLevel
from pyquil.gates import H, CNOT
from pyquil.paulis import sX, sY, sZ

ansatz = Program(H(0), CNOT(0, 1)).wrap_in_numshots_loop(32)
settings = [
    ExperimentSetting(plusZ(0) * plusZ(1), sX(0) * sX(1)),
    ExperimentSetting(plusZ(0) * plusZ(1), sX(0)),
    ExperimentSetting(plusZ(0) * plusZ(1), sZ(0)),
]
base = Experiment(
    settings, ansatz,
    symmetrization=SymmetrizationLevel.EXHAUSTIVE,
)
```

1. Confirm `base.shots == 32`, `base.get_meas_qubits()` is `[0, 1]`, and all
   measured qubits are integer ids.
2. Call `base.generate_experiment_program()` before grouping. Inspect the
   generated declarations and measurement order. This is construction only.
3. Call `group_settings(base, method="greedy")` or
   `method="clique-removal"`. For each inner list, verify that no qubit has two
   different requested input eigenstates or two different output axes. Do not
   infer compatibility solely from commutation.
4. Keep the singleton `base` for `generate_calibration_experiment()` because
   that method rejects grouped settings. Use the grouped copy only with a path
   that explicitly supports grouped settings.
5. Record whether each observable coefficient is real and whether the requested
   calibration denominator is expected to be nonzero.

**Expected observations:** grouping reduces the number of inner groups only when
local bases match; grouping is a planning transformation and does not sample
anything.

## 5. Prepare calibration and symmetrization, then stop safely

For the ungrouped `base` above:

```python
calibration = base.generate_calibration_experiment()
cal_program = calibration.generate_experiment_program()
setting_map = base.build_setting_memory_map(base[0][0])
symm_maps = base.build_symmetrization_memory_maps([0, 1])
```

Validate that `calibration.calibration == CalibrationMethod.NONE`, its settings
measure the same observables in their plus eigenstates, and exhaustive
symmetrization creates four two-qubit memory maps (`[0,0]`, `[0,pi]`,
`[pi,0]`, `[pi,pi]`). These values describe generated runtime memory maps; they
are not results.

If the chosen policy is non-exhaustive, expect calibration to be disabled by
the `Experiment` constructor or rejected by the calibration generator. If the
chosen path is `QuantumComputer.run_experiment`, use singleton settings because
4.18.0 rejects grouped settings. If the chosen path is
`pyquil.operator_estimation.measure_observables`, grouped settings are
supported, but `qc.run_symmetrized_readout` still requires a configured QVM/QPU
or a deliberately constructed local backend. Stop with an explicit prerequisite
message when no backend is available.

## 6. Interpret synthetic results

Use a deterministic bitstring array to validate the convention before consuming
backend output:

```python
from pyquil.experiment import bitstrings_to_expectations
bits = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
values = bitstrings_to_expectations(bits, joint_expectations=[[0], [1], [0, 1]])
# columns are <Z0>, <Z1>, and <Z0 Z1>
```

The first two columns are `+1,-1` mappings per bit and the last is their rowwise
product. For an `ExperimentResult`, report `expectation`, `std_err`, and
`total_counts` together. If calibration is applied, retain the raw and
calibration fields and state the ratio assumption. A corrected expectation
outside the physical interval is a warning about sampling/conditioning, not a
reason to silently clamp it.

## 7. Pauli exponentiation choice

Choose based on the requested output:

- Need Quil instructions, placeholders, or runtime angle: `exponential_map`.
- Need a commuting product of Quil evolutions: `exponentiate_commuting_pauli_sum`
  after verifying commutation.
- Need an approximation for noncommuting terms: `trotterize`, with explicit
  order and steps.
- Need a small dense unitary and fixed integer qubits: `exponentiate_pauli_sum`.

Check the convention (`alpha` versus `pi` cycles), coefficient reality, and
exponential scaling before generating a large matrix or program.
