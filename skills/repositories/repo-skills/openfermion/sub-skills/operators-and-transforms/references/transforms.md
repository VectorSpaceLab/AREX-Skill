# Fermion, Majorana, and binary-code transforms

## Mapping choice

| Need | Use | Input | Important contract |
| --- | --- | --- | --- |
| Canonical, broad, easy-to-audit map | `jordan_wigner(op)` | `FermionOperator`, `MajoranaOperator`, `InteractionOperator`, or diagonal Coulomb representation | Computes the minimum output support from the input; there is no public `n_qubits` parameter. |
| Fenwick-tree map from the original BK paper/2012 convention | `bravyi_kitaev(op, n_qubits=None)` | `FermionOperator`, `MajoranaOperator`, or `InteractionOperator` | `n_qubits` may pad fermion/Majorana transforms but must not be below the required count. |
| Alternative tree convention | `bravyi_kitaev_tree(op, n_qubits=None)` | Fermion-like operator expected by the implementation | Distinct from `bravyi_kitaev` when the mode count is not a power of two. |
| Explicit occupation encoding | `binary_code_transform(fermion_op, code)` | `FermionOperator` plus `BinaryCode` | Code fixes `n_modes` and output qubit count; nonlinear codes may expand terms substantially. |
| Reverse the JW representation | `reverse_jordan_wigner(qubit_op, n_qubits=None)` | `QubitOperator` only | Produces a `FermionOperator`; no general reverse BK/binary transform exists here. |
| Hamiltonian-only edge encoding | `bravyi_kitaev_fast(op)` | Hermitian `InteractionOperator` | BKSF/BK-fast is not a general arbitrary-fermion transform and uses an interaction graph encoded by the Hamiltonian. |

All maps preserve algebraic action but generally change the Pauli term
 dictionary. Validate equivalence by canonicalizing and comparing a small
 sparse matrix or spectrum in a common dimension, not by comparing raw strings.

## Jordan-Wigner

The package implements the convention

```text
 a_j^ = Z_0 ... Z_(j-1) (X_j - i Y_j) / 2
 a_j  = Z_0 ... Z_(j-1) (X_j + i Y_j) / 2
```

For example, a Hermitian hopping term has a compact expected image:

```python
from openfermion import FermionOperator, jordan_wigner

hopping = FermionOperator("1^ 0", 0.5) + FermionOperator("0^ 1", 0.5)
assert jordan_wigner(hopping).terms == {
    ((0, "X"), (1, "X")): 0.25,
    ((0, "Y"), (1, "Y")): 0.25,
}
```

The actual coefficient values may be `complex`/NumPy scalar equivalents, so
prefer `isclose` or coefficient-wise approximate checks in reusable code.
JW also maps a Majorana index `2*q` to the X-ending JW string and `2*q+1` to
the Y-ending string, with the same prefix of Z factors. A constant-only input
maps to a Qubit identity with its constant; a zero operator maps to zero.

`jordan_wigner_one_body(p, q, coefficient=1.0)` and
`jordan_wigner_two_body(p, q, r, s, coefficient=1.0)` are specialized helpers
for a term plus its Hermitian conjugate. They assume the associated
Hermitian-pair interpretation and halve diagonal contributions; they are not
generic replacements for `jordan_wigner(FermionOperator(...))`.

`jordan_wigner` has no `n_qubits=` keyword. If an output must occupy a padded
space, map first and pass `n_qubits` to `get_sparse_operator` or use a suitable
explicit code/transform. Passing `n_qubits` directly to `jordan_wigner` raises
`TypeError`.

## Bravyi-Kitaev variants

`bravyi_kitaev` uses the update, occupation, and parity sets associated with a
Fenwick tree and the original Bravyi-Kitaev convention. The optional
`n_qubits` is useful when a `FermionOperator` or `MajoranaOperator` only touches
some low modes but the full simulation space must be retained:

```python
from openfermion import FermionOperator, bravyi_kitaev, count_qubits

op = FermionOperator("1^ 0")
assert count_qubits(op) == 2
mapped = bravyi_kitaev(op, n_qubits=4)
```

A smaller value raises `ValueError("Invalid number of qubits specified.")`.
Keep `n_qubits` at least `count_qubits(op)` and nonnegative. For a fixed
`InteractionOperator`, use its tensor dimension as the count; the specialized
implementation assumes the interaction tensor shape and should not be treated
as a free padding mechanism.

`bravyi_kitaev_tree` implements the arXiv:1701.07072 tree variant for a
`FermionOperator`. It is intentionally not interchangeable with
`bravyi_kitaev` for non-power-of-two mode counts. Choose one convention once
for a recovery or comparison and do not mix their expected Pauli terms. `symmetry_conserving_bravyi_kitaev` is a
separate specialized transform for an active fermionic Hamiltonian; it has
assumptions about active orbitals/fermions and is not the generic BK API.

`bravyi_kitaev_fast`/`bravyi_kitaev_fast_interaction_op` accept only an
`InteractionOperator`, require a Hermitian Hamiltonian structure, and derive
an edge matrix from its one- and two-body terms. Use them only when the task
explicitly requires BKSF/BK-fast; for arbitrary `FermionOperator` terms use
standard JW/BK or a binary code.

## Binary codes

A `BinaryCode(encoding, decoding)` relates an occupation vector of length
`n_modes` to a qubit vector of length `n_qubits`. Its public properties are
`.encoder` (a SciPy sparse matrix), `.decoder` (a list of `BinaryPolynomial`),
`.n_modes`, and `.n_qubits`. The code constructor validates dimensions and
referenced qubit indices. Useful built-ins are:

```python
from openfermion import (
    binary_code_transform, bravyi_kitaev_code, checksum_code,
    interleaved_code, jordan_wigner_code, parity_code,
    weight_one_binary_addressing_code, weight_one_segment_code,
    weight_two_segment_code,
)

fermion = ...
custom_jw = binary_code_transform(fermion, jordan_wigner_code(4))
custom_parity = binary_code_transform(fermion, parity_code(4))
custom_bk = binary_code_transform(fermion, bravyi_kitaev_code(4))
```

`jordan_wigner_code(n_modes)` has equal mode/qubit counts and should agree with
`jordan_wigner` for the same fermionic operator. `bravyi_kitaev_code(n_modes)`
encodes the standard BK convention. `parity_code(n_modes)` has equal counts
but stores cumulative parity. `checksum_code(n_modes, odd)` saves one qubit for
a fixed even/odd Hamming-weight sector. The weight-one and weight-two codes
are nonlinear, sector-specific, and can produce many terms; use only when the
state-space restriction is part of the problem. `interleaved_code(modes)`
requires an even mode count and changes orbital ordering.

`binary_code_transform` rejects non-`FermionOperator` inputs and non-
`BinaryCode` codes. It decomposes logical multi-qubit expressions into Pauli
strings, so a code can be correct while producing far more terms than JW/BK.
An operator index outside `0..code.n_modes-1` is a code/data mismatch, not a
request for automatic padding. Check `count_qubits(fermion) <= code.n_modes`
before calling.

## Reverse JW and round trips

```python
from openfermion import QubitOperator, jordan_wigner, reverse_jordan_wigner

q = QubitOperator("X0 Y1 Z2", 0.25) + QubitOperator("Z1", -0.4)
f = reverse_jordan_wigner(q, n_qubits=3)
back = jordan_wigner(f)
back.compress()
```

There is no top-level `compress` function; call `back.compress()`. The reverse
map uses `Z_j -> I - 2 a_j^ a_j` and expands X/Y factors with JW parity
strings. Its `n_qubits` must be at least `count_qubits(q)`, but the returned
fermionic operator may only have support on modes that the Pauli term touches.
Only X/Y/Z factors are valid; an identity is represented by an empty term.
Round-trip equality should use `back.isclose(q)` after compression, allowing
for small floating-point residue.

## Qubit-count and sparse validation

There are three different counts to keep separate:

1. `count_qubits(op)`: minimum support inferred from data.
2. A transform's explicit `n_qubits`: optional padded mapping space, supported
   by standard BK and reverse JW (not by the public JW function).
3. A `BinaryCode`'s fixed `n_modes`/`n_qubits`: the code contract.

For a matrix of dimension `2**N`, make `N` explicit at the sparse boundary:

```python
from openfermion.linalg import get_sparse_operator

q = jordan_wigner(FermionOperator("1^ 0") + FermionOperator("0^ 1"))
matrix = get_sparse_operator(q, n_qubits=4)  # shape (16, 16)
```

Passing too few qubits to a sparse conversion raises a validation error. A
matrix-shape difference between otherwise equivalent maps is often just a
missing explicit padding argument.

## Lightweight mapping checks

For `a_p` and `a_q^`, check the CAR on a small common space:

```python
from openfermion import FermionOperator, anticommutator, jordan_wigner, QubitOperator

a = jordan_wigner(FermionOperator("1"))
adag = jordan_wigner(FermionOperator("1^"))
assert anticommutator(a, adag) == QubitOperator(())
```

For a full check, use distinct and equal modes and verify that annihilator-
annihilator anticommutators vanish, equal-mode annihilator/creator gives the
identity, and number operators commute. These checks distinguish an ordering
or sign convention error from an accidental term-string mismatch.
