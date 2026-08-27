# States, ordering, observables, and sampling

Read this reference whenever a result must be compared across simulator
implementations or translated into bitstrings, matrices, or Pauli expectations.

## Canonical basis and the q0 trap

The canonical flat vector order is lexicographic `00, 01, 10, 11, ...`, while
qubit 0 is the least-significant/rightmost bit. For two qubits:

| Flat index | Label | Physical assignment |
|---:|---|---|
| 0 | `00` | q1=0, q0=0 |
| 1 | `01` | q1=0, q0=1 |
| 2 | `10` | q1=1, q0=0 |
| 3 | `11` | q1=1, q0=1 |

Therefore `X(0)` has the flat vector `[0, 1, 0, 0]`, while `X(1)` has
`[0, 0, 1, 0]`. This is also the ordering used by `Wavefunction.amplitudes`,
`probabilities()`, and `get_outcome_probs()` keys.

`ReferenceWavefunctionSimulator.wf` follows that flat convention. The NumPy
simulator instead stores an n-dimensional tensor with q0 on the leftmost axis:
for `X(0)` its tensor is `[[0, 0], [1, 0]]`; for comparison with a canonical
flat vector reverse axes first:

```python
canonical = numpy_sim.wf.transpose().reshape(-1)
```

For arbitrary n, `transpose()` with no axes reverses the axes. Do not use a
plain `reshape(-1)` as a cross-backend comparison unless you intentionally want
the NumPy tensor-axis order.

## Wavefunction outputs

Use numerical APIs rather than display strings:

```python
probs = wavefunction.probabilities()
by_label = wavefunction.get_outcome_probs()
rounded = wavefunction.pretty_print_probabilities(decimal_digits=6)
text = wavefunction.pretty_print(decimal_digits=6)
```

`probabilities()` has length `2**n` and sums to one for a valid
`Wavefunction`. Display helpers round and suppress values that round to zero.
The constructor rejects a vector whose length is not a positive power of two or
whose probability sum is not one.

Sampling has three conventions to keep separate:

1. `ReferenceWavefunctionSimulator.sample_bitstrings` and
   `ReferenceDensitySimulator.sample_bitstrings` use the canonical probability
   vector and flip the lexicographic columns so returned column 0 is q0.
2. `NumpyWavefunctionSimulator.sample_bitstrings` returns an array of shape
   `(n_samples, n_qubits)` with q0 in column 0, consistent with its tensor
   convention.
3. `Wavefunction.sample_bitstrings` samples from the `Wavefunction` object
   using the global NumPy RNG and returns lexicographic product rows. For
   service calls, prefer `WavefunctionSimulator.run_and_measure(...,
   qubits=[...])`, whose returned columns follow the explicit `qubits` list.

When order matters, create a deterministic basis-state test such as `X(0)`,
assert both the vector index and the sampled row, and document whether rows are
labels or requested-qubit columns. For stochastic direct simulators, provide
`rs=np.random.RandomState(seed)` or use `PyQVM(seed=seed)`; without `rs`,
measurement and sampling raise `ValueError` about a missing random state.

## Expectations

Wavefunction simulators accept `PauliTerm` or `PauliSum`:

```python
from pyquil.paulis import sX, sY, sZ

xx = sX(0) * sX(1)
yy = sY(0) * sY(1)
zz = sZ(0) * sZ(1)
assert np.isclose(reference.expectation(xx), 1.0)
assert np.isclose(reference.expectation(yy), -1.0)
assert np.isclose(reference.expectation(zz), 1.0)
```

A `PauliSum` is summed term-by-term. Terms with non-integer qubit designators
or unsupported coefficient forms can fail in the reference implementation;
normalize the operator to integer-qubit `PauliTerm`s before calling the
simulator boundary.

`ReferenceDensitySimulator` has no implemented `expectation` method in this
version. For a controlled local diagnostic, build the full operator with
`lifted_pauli` and compute:

```python
operator = lifted_pauli(zz, qubits=[0, 1])
value = np.trace(density_sim.density @ operator)
```

For `qubits=[0, 1]`, `lifted_pauli` constructs the matrix in the same canonical
little-endian ordering; a Pauli on q0 is the right Kronecker factor. Use
`np.real_if_close(value)` and check Hermiticity before treating a result as a
real expectation. Do not present this as the density simulator's
`.expectation()` API or as a complete Experiment workflow.

## Density validation

`ReferenceDensitySimulator.set_initial_state(state_matrix)` requires a square
matrix whose dimension is exactly `2**n_qubits`. It then requires:

- Hermitian: `rho == rho.conj().T` within tolerance;
- trace one: `np.trace(rho) == 1` within tolerance;
- no materially negative eigenvalues (positive semidefinite).

A valid pure state is `np.outer(psi, psi.conj())` for a normalized length
`2**n` vector. After each unitary or supported Kraus update, validate:

```python
assert rho.shape == (2**n, 2**n)
assert np.allclose(rho, rho.conj().T)
assert np.isclose(np.trace(rho), 1.0)
```

Do not use a wavefunction-shaped `(2,)*n` tensor as a density matrix or pass a
matrix for a different qubit count.

## Matrix tools and ordering probes

- `all_bitstrings(n)` returns the lexical table used to map indices to rows.
- `get_measure_probabilities(wf, qubit)` sums all axes except the selected
  NumPy tensor axis and returns the two probabilities for that qubit.
- `lifted_gate_matrix` embeds a 1Q/2Q/... matrix into the full Hilbert space,
  including nonadjacent qubits by a permutation. The order of `qubit_inds`
  is the gate's argument order; swapping it can change a controlled gate.
- `program_unitary` accepts only gates (and HALT), returns a `(2**n, 2**n)`
  matrix, and rejects declarations or measurements. It is useful for a
  deterministic unitary cross-check, not for a program with classical paths.
- `unitary_equal` compares same-shape matrices up to global phase; it is not a
  substitute for checking the state vector's global phase when amplitudes are
  consumed directly.

For a suspected ordering bug, test all of `X(0)`, `X(1)`, and a Bell program,
then compare (a) reference flat vector, (b) NumPy tensor after axis reversal,
(c) probability labels, and (d) explicitly ordered measurement columns.
