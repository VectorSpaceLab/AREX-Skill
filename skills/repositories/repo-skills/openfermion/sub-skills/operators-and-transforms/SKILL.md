---
name: operators-and-transforms
description: "Operate on OpenFermion's symbolic and tensor operator
  representations, normalize and validate terms, and choose or apply
  fermion-to-qubit mappings."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Operators and transforms

Use this sub-skill when a task needs second-quantized operator algebra, Pauli
strings, Majorana or bosonic ladder operators, tensor-backed interaction
representations, normal ordering, Hermitian checks, commutators/BCH terms, or a
fermion-to-qubit mapping. It covers the public OpenFermion APIs and small,
inspectable operators; route model construction and chemistry file formats to
[hamiltonians-and-chemistry](../hamiltonians-and-chemistry/SKILL.md), circuit
synthesis/simulation to [circuits-and-simulation](../circuits-and-simulation/SKILL.md),
and large eigensolvers or RDM workflows to
[analysis-and-measurements](../analysis-and-measurements/SKILL.md).

## Fast route

1. **Identify the representation.** Use `FermionOperator` for arbitrary
   fermionic ladder-polynomials, `QubitOperator` for sums of Pauli strings,
   `BosonOperator` for bosonic ladders, and `MajoranaOperator` for products of
   Majorana generators. Use `InteractionOperator` or `PolynomialTensor` only
   when fixed tensor structure and array operations are useful.
2. **Construct with explicit conventions.** Fermion/boson strings use `p^` for
   creation and `p` for annihilation. Qubit strings use `X0`, `Y1`, or `Z2`.
   The empty string/tuple is identity; a no-argument constructor is zero.
   Keep the factor order of fermionic terms until `normal_ordered` is called.
3. **Validate before mapping.** Check `count_qubits(op)`,
   `is_hermitian(op)`, and the relevant number-preservation predicate. For
   malformed input, inspect index/action types first; see
   [troubleshooting](references/troubleshooting.md).
4. **Choose a map deliberately.** Use `jordan_wigner` for the direct canonical
   mapping and broad compatibility; `bravyi_kitaev` for a Fenwick-tree mapping
   with an optional explicit qubit count; `binary_code_transform` for a
   supplied `BinaryCode` (including parity, checksum, or qubit-saving codes).
   Use `reverse_jordan_wigner` only for the JW inverse direction.
5. **Compare representations, not term dictionaries.** JW and BK generally
   produce different Pauli strings but represent equivalent operators. Compare
   spectra or sparse matrices only after choosing the same Hilbert-space size.
6. **Cross the sparse boundary intentionally.** Use `get_sparse_operator` only
   after mapping/normalization and pass `n_qubits` for padded fermion/qubit
   spaces. For bosons, pass a finite `trunc`; this is a Fock-space cutoff, not
   a qubit count.

## Core recipes

```python
from openfermion import (
    FermionOperator, QubitOperator, bravyi_kitaev, count_qubits,
    hermitian_conjugated, jordan_wigner, normal_ordered,
)

hop = FermionOperator("0^ 1", 0.5)
hop += hermitian_conjugated(hop)
hop = normal_ordered(hop)
assert hop.is_normal_ordered()
print(count_qubits(hop))                 # 2
jw = jordan_wigner(hop)                  # 0.25 [X0 X1] + 0.25 [Y0 Y1]
bk = bravyi_kitaev(hop, n_qubits=2)      # equivalent, different strings
```

Use `op.terms` for programmatic inspection. Its keys are tuples of
`(index, action)` pairs: `(index, 1)`/`(index, 0)` for creation/annihilation and
`(index, "X"|"Y"|"Z")` for Pauli factors. `+=`, `-=`, `*=`, and `/=` mutate;
ordinary arithmetic returns a copy. Same-type products are algebraically
simplified, including Pauli phases. `compress()` removes near-zero terms;
`isclose(other, rtol=..., atol=...)` is preferable to comparing printed text.

For a quick CPU-only smoke check from any working directory, run the bundled
[smoke_transform.py](scripts/smoke_transform.py) helper:

```bash
python scripts/smoke_transform.py --help
python scripts/smoke_transform.py --mapping jw --sparse
```

The helper uses only public imports, a two-mode hopping term, and a tiny sparse
matrix; it does not read source files or use the network.

## Decision points and boundaries

- `normal_ordered` is a representation rewrite using canonical
  anti-commutation/commutation relations; it can increase term count and is
  exponential in the locality of a ladder term. For chemistry-style
  two-body operators, `chemist_ordered` requires a two-body,
  number-conserving `FermionOperator`.
- `InteractionOperator` assumes a number-conserving, Hermitian interaction
  Hamiltonian structure. It is not a general replacement for an arbitrary
  `FermionOperator`; use the latter for non-Hermitian or non-number-conserving
  expressions.
- `jordan_wigner` maps `FermionOperator`, `MajoranaOperator`,
  `InteractionOperator`, and diagonal Coulomb representations, but has no
  `n_qubits` argument. `bravyi_kitaev` accepts `FermionOperator`,
  `MajoranaOperator`, and `InteractionOperator`; its `n_qubits` may pad the
  first two kinds. Never pass a value below `count_qubits`.
- Custom binary codes are constrained by the code's `n_modes` and
  `n_qubits`; they are not a general way to pad an operator. Nonlinear or
  qubit-saving codes can expand a term into many Pauli strings.
- `reverse_jordan_wigner` accepts only a `QubitOperator` and returns a
  `FermionOperator`; it is not a general inverse for BK or arbitrary binary
  codes. Round-trip after `compress()` is the useful correctness check.
- Sparse conversion is a representation boundary, not a solver. Keep large
  eigenspectrum, ground-state, RDM, measurement, and model-builder work in the
  routed sub-skills.

For signatures, term schemas, tensor indexing, and concrete expected outputs,
read [api-reference.md](references/api-reference.md). For mapping formulas,
variants, qubit-count rules, and binary-code choices, read
[transforms.md](references/transforms.md). For failure diagnosis, read
[troubleshooting.md](references/troubleshooting.md).

## Recovery guidance

When recovering an operator transformation from partial notes, first reconstruct
the exact term tuple and coefficient, then normal-order it and record
`count_qubits`. Build the smallest Hermitian hopping or number-operator fixture,
map it with JW and the selected alternative, and compare canonical algebra
(`commutator`/`anticommutator`), term counts, and—when feasible—small sparse
matrices. Do not infer a BK or binary-code qubit count from a printed term:
carry the explicit `n_qubits`/code dimensions through the experiment. Preserve
whether a mismatch is a convention issue (mode order, creation order, or
Majorana indexing), an invalid input, or a true transform limitation.
