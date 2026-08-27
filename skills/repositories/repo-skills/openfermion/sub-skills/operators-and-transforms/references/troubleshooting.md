# Troubleshooting operators and transforms

## Install and import

- **`ModuleNotFoundError: openfermion`**: verify that the package is installed
  in the interpreter running the task and that the import is from the public
  package namespace. Do not solve this by importing repository-relative source
  modules. A minimal CPU operator workflow needs NumPy; sparse conversion also
  needs SciPy.
- **Import fails while loading optional chemistry/model modules**: keep this
  workflow focused on `openfermion.ops`, `openfermion.transforms`,
  `openfermion.utils`, and `openfermion.linalg`. Chemistry backends, molecular
  file readers, and model-specific plugins belong to the routed chemistry
  skill and are not required for core symbolic algebra or JW/BK checks.
- **Version-sensitive signature or warning**: inspect
  `openfermion.__version__` and `inspect.signature` in the active environment.
  In the inspected release, `jordan_wigner` has no `n_qubits` keyword,
  `bravyi_kitaev`/`bravyi_kitaev_tree` use `n_qubits=None`, and
  `PolynomialTensor.rotate_basis(..., transpose=None)` emits a deprecation
  warning about its current default.

## Optional dependency and backend issues

- **Sparse conversion import/runtime error**: `get_sparse_operator` returns a
  SciPy CSC matrix. Install/verify SciPy for this boundary; the symbolic
  classes and transforms themselves do not require a GPU backend.
- **Boson sparse conversion fails or is enormous**: provide a finite `trunc`
  to `get_sparse_operator`. Bosonic Fock space is infinite without truncation,
  and the resulting dimension grows as `trunc ** n_modes`; reduce the tiny
  smoke case rather than silently launching a large workload.
- **BKSF/BK-fast unavailable for the input**: `bravyi_kitaev_fast` is restricted
  to Hermitian `InteractionOperator` inputs. It is not a fallback for an
  arbitrary `FermionOperator`; choose standard JW/BK or convert only when the
  interaction assumptions are actually satisfied.
- **Unexpected backend requirement**: JW, BK, binary-code transforms, normal
  ordering, and commutator/BCH algebra are CPU symbolic operations. GPU,
  vendor accelerator, network, and chemistry-plugin setup is outside this
  sub-skill; route or narrow the task instead of adding optional extras.

## Data and configuration validation

- **Malformed factor/index**: indices must be non-negative integers. Fermion
  and boson actions are `1`/`0`; Qubit actions are exactly `X`, `Y`, or `Z`.
  Typical diagnostics are `ValueError: Invalid index in factor ...` or
  `Invalid action in factor ...`. Use internal tuple order `(index, action)`;
  the human-readable Qubit string is action-before-index (`X0`), while a
  Fermion string is index-before-action (`0^`).
- **Identity mistaken for zero**: `FermionOperator("")` or
  `FermionOperator(())` is identity; `FermionOperator()` is zero. Check
  `op.terms` and `op.constant` instead of relying on a blank printout.
- **Wrong tensor shape**: `InteractionOperator` needs a square one-body array
  and a rank-4 two-body array with the same `n_qubits`. `PolynomialTensor` keys
  describe action patterns and every associated tensor needs compatible
  dimensions. Use `tensor.n_qubits` and inspect `n_body_tensors.keys()` before
  arithmetic or basis rotation.
- **Lost fermionic sign**: term order is meaningful for fermions. Do not sort
  fermionic factors by index manually. Call `normal_ordered` and compare the
  resulting operator, not a hand-reordered tuple. For Majoranas, remember that
  the constructor canonicalizes and may introduce a sign.
- **Non-Hermitian interaction representation**: `InteractionOperator` is
  intended for a Hermitian, number-conserving interaction Hamiltonian. Keep an
  arbitrary or pairing/non-number-conserving expression as a
  `FermionOperator` until a representation explicitly supports it.

## API and misuse errors

- **`TypeError` from mixed arithmetic/commutator**: symbolic arithmetic and
  `commutator`/`anticommutator` require same-type operators. Map both operands
  first or convert both to a common representation.
- **`normal_ordered` rejects the object**: the public helper supports
  `FermionOperator`, `BosonOperator`, `QuadOperator`, and `InteractionOperator`.
  It does not directly normal-order `QubitOperator` or `MajoranaOperator`.
- **`chemist_ordered` rejects the object**: the input must pass
  `is_two_body_number_conserving()`; it is not a generic fermionic reorderer.
  Check term lengths, equal creation/annihilation counts, and (if requested)
  spin symmetry.
- **`n_qubits` validation failure**: for BK and reverse JW, a requested count
  below `count_qubits(input)` raises `ValueError`. JW does not accept this
  argument. For sparse conversion, pass the count there instead. Keep code
  dimensions separate from minimum support.
- **Binary code mismatch**: `binary_code_transform` requires a
  `FermionOperator` and `BinaryCode`; every fermionic index must be below
  `code.n_modes`. Check `code.n_modes`, `code.n_qubits`, and the decoder before
  calling. A code-saving mapping is valid only for the encoded sector.
- **No inverse for BK**: `reverse_jordan_wigner` only reverses the JW
  convention. Do not label its output as a BK inverse or expect a binary-code
  round trip without retaining the code and its sector assumptions.
- **Unexpected equality result**: `==` is approximate for symbolic operators,
  but a mathematically equivalent operator may have residual tiny terms. Call
  `.compress()` before comparing, or use `.isclose(rtol=..., atol=...)`.
  `is_identity` checks a symbolic empty term and does not inspect a matrix.
- **Tensor rotation changes the wrong basis**: pass `transpose=True` or
  `transpose=False` explicitly to `rotate_basis` and record the convention.
  The call mutates the tensor and returns `None`; a missing assignment is
  expected.

## Workflow-specific failures and recovery

- **JW/BK term mismatch**: first check mode ordering, whether the input was
  normal ordered, coefficient conjugation, and whether standard BK or tree BK
  was requested. Compare a small sparse matrix/spectrum with the same explicit
  dimension; raw Pauli-term dictionaries should differ.
- **Mixed operator terms**: do not call one transform on a sum that mixes
  unsupported classes. Normalize each component to a supported common class
  (`FermionOperator` for JW/BK) and record the conversion. If the sum combines
  a fixed tensor Hamiltonian with arbitrary terms, keep the arbitrary portion
  separate or route representation conversion to the appropriate skill.
- **Malformed term in a generated/recovered request**: isolate the smallest
  failing factor, reconstruct it with a tuple, and check `type(index)`, index
  sign, and action spelling. A request such as `Q0`, `-1`, or `0x` is a data
  error, not evidence that the mapper is unavailable.
- **CAR or commutator check fails**: test equal-mode and distinct-mode ladder
  pairs separately. For fermions, call `normal_ordered` on algebraic products;
  for bosons, use the `parity=1` commutation convention through
  `normal_ordered`. Confirm that operators are the same class before
  `commutator`/`anticommutator`.
- **Round trip grows unexpectedly**: reverse JW expands Pauli factors into
  ladder terms, and normal ordering may add contractions. This is expected for
  nonlocal Pauli strings. Keep the fixture tiny, compress only after the full
  map, and record term counts rather than assuming term-by-term identity.
- **Sparse matrix has the wrong shape**: calculate the desired Hilbert-space
  size explicitly. `count_qubits` reports minimum support, not the requested
  simulation size. Pass `n_qubits=N` for a `2**N` qubit matrix; pass `trunc` for
  bosonic modes. Never fix this by adding unused high-index terms to the
  operator.
- **Normal ordering becomes expensive**: bound the input locality and term
  count. Use tensor-specific or structure-specific paths for large
  interaction data, and route large-scale analysis away from this sub-skill.
  Do not raise `order` in `bch_expand` or expand a binary code without a small
  deterministic fixture and an explicit budget.
- **Recovery cannot decide a mapping**: preserve both JW and the selected
  alternative as hypotheses. Verify canonical anticommutation, Hermiticity,
  minimum/padded qubit counts, and a tiny matrix before choosing. If the source
  only says “Bravyi-Kitaev,” record whether it means standard `bravyi_kitaev`,
  `bravyi_kitaev_tree`, BK-fast, or a `bravyi_kitaev_code` binary transform.

There is no package CLI required for these operations. A command-line failure
from a downstream script is therefore usually an invocation/configuration
problem in that script; reproduce the core operation with the bundled
`scripts/smoke_transform.py` and public Python calls first.
