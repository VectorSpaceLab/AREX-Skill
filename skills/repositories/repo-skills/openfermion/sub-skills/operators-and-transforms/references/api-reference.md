# Operator and utility API reference

The public exports used here are available from `openfermion`, or from the
more focused `openfermion.ops`, `openfermion.transforms`,
`openfermion.utils`, and `openfermion.linalg` namespaces. The inspected package
reports version `1.8.2.dev0`; check the installed version when exact behavior
matters.

## Term schemas

| Class | String factor syntax | Internal factor/key | Algebra and identity |
| --- | --- | --- | --- |
| `FermionOperator` | `"3^ 1"` | `(3, 1)` creation, `(1, 0)` annihilation | Different mode factors do **not** commute; order is meaningful. |
| `BosonOperator` | `"3^ 1"` | Same `(index, action)` encoding | Different mode factors commute; same-mode commutators matter. |
| `QubitOperator` | `"X0 Y3 Z4"` | `(0, "X")`, `(3, "Y")`, `(4, "Z")` | Factors on different qubits commute; same-qubit Pauli products carry phases. |
| `MajoranaOperator` | no string parser | a term is a tuple such as `(0, 2, 5)` | Majorana indices are canonicalized; repeated indices cancel with the Clifford sign rule. |

For `FermionOperator` and `BosonOperator`, `1` means raising/creation and `0`
means lowering/annihilation. Indices must be non-negative Python integers. For
`QubitOperator`, actions are exactly `"X"`, `"Y"`, or `"Z"`; identity factors
are normally omitted. A factor sequence uses internal order, for example:

```python
FermionOperator(((3, 1), (1, 0)), 0.5)
QubitOperator(((0, "X"), (2, "Z")), 0.5)
MajoranaOperator((0, 3), -1j)
```

`FermionOperator(())`, `FermionOperator("")`, and the corresponding empty
term for the other symbolic classes are multiplicative identities. A no-arg
constructor is the additive zero. `terms` is the authoritative dictionary;
for symbolic operators its keys are term tuples and values are coefficients.

## Construction, arithmetic, and inspection

The common constructor is `Class(term=None, coefficient=1.0)`. Supplying the
coefficient at construction avoids an unnecessary copy compared with scalar
multiplication. Symbolic classes support same-type `+`, `-`, `*`, scalar
multiplication/division, `**` for a non-negative integer, and in-place forms.
A scalar added to or subtracted from a symbolic operator changes its constant
term. Cross-class arithmetic is rejected.

Useful methods and properties:

| API | Practical use and caveat |
| --- | --- |
| `Class.zero()` / `Class.identity()` | Explicit additive/multiplicative identities. |
| `.constant` | Read or set the empty-term coefficient. Setting it to zero does not necessarily remove the key until compression/addition logic runs. |
| `.compress(abs_tol=1e-8)` | Removes small coefficients and strips negligible real/imaginary parts in symbolic operators. Mutates and returns `None`. |
| `.isclose(other, tol=None, rtol=1e-8, atol=1e-8)` | Termwise approximate comparison. `tol` is deprecated and cannot be combined with `rtol`/`atol`. `==` delegates to approximate comparison for symbolic operators. |
| `.induced_norm(order=1)` | Coefficient p-norm, not a matrix/operator norm. |
| `.many_body_order()` | Maximum nonzero term length; zero operator gives `0`. |
| `.get_operators()` | Generator of one-term operators. `.get_operator_groups(n)` groups terms for controlled decompositions. |
| `.terms` iteration | Iterating a symbolic operator yields one-term instances; direct dictionary iteration is more predictable for serialization/inspection. |
| `QubitOperator.renormalize()` | Mutates by dividing by its coefficient induced 2-norm; raises on zero/empty operator. |
| `FermionOperator.is_normal_ordered()` | Tests the package's descending-index, creators-first convention. |
| `FermionOperator.is_two_body_number_conserving(check_spin_symmetry=False)` | Accepts term lengths 0, 2, or 4 and equal creation/annihilation counts; optional spin-parity check. |
| `BosonOperator.is_normal_ordered()` | Tests creators-first order with same-mode index ordering. |
| `BosonOperator.is_boson_preserving()` | Requires balanced creation/annihilation count in each term. |
| `MajoranaOperator.from_dict(mapping)` | Fast constructor, but deliberately performs no validation. Validate data before using it. `.commutes_with(other)` handles scalars and same-type operators. |

A common Hermitian construction is:

```python
term = FermionOperator("2^ 0", 0.75)
hermitian_term = term + hermitian_conjugated(term)
assert is_hermitian(hermitian_term)
```

`hermitian_conjugated` reverses factor order and swaps creation/annihilation
for fermions and bosons; it conjugates coefficients. Qubit factors remain in
place and coefficients are conjugated. It also supports `InteractionOperator`,
NumPy arrays, and SciPy sparse matrices. `is_hermitian` normal-orders ladder
operators before comparison, while Qubit operators use direct approximate
comparison. `is_identity` supports Qubit/Fermion/Boson/Quad symbolic classes
and means exactly one empty term, not a scalar matrix test.

## Cross-representation conversion

The public conversion helpers are useful when a specialized transform accepts a
representation different from the current one:

| API | Direction and supported inputs |
| --- | --- |
| `get_fermion_operator(operator)` | `PolynomialTensor`, diagonal Coulomb representation, or `MajoranaOperator` to `FermionOperator`. |
| `get_majorana_operator(operator)` | `FermionOperator`, `PolynomialTensor`, or diagonal Coulomb representation to `MajoranaOperator`; uses even/odd Majorana indices per fermionic mode. |
| `get_quad_operator(operator, hbar=1.0)` | `BosonOperator` to `QuadOperator`, using `[q_i,p_j]=i*hbar*delta_ij`. |
| `get_boson_operator(operator, hbar=1.0)` | `QuadOperator` to `BosonOperator` with the same `hbar` convention. |
| `check_no_sympy(operator)` | Raises if symbolic coefficients contain SymPy expressions that the tensor/diagonal conversions cannot handle. |

These helpers are algebraic conversions, not chemistry or file I/O. Preserve
`hbar` when converting boson/quad operators in both directions. For a custom
Majorana term, remember that even index `2*k` and odd index `2*k+1` derive from
fermionic mode `k`; do not use a separate one-based convention.

## Normal ordering and operator utilities

```python
from openfermion import (
    FermionOperator, BosonOperator, chemist_ordered, normal_ordered,
    reorder,
)

raw = FermionOperator("1 0^", 2.0)
ordered = normal_ordered(raw)       # 2.0 [] - 2.0 [0^ 1]
assert ordered.is_normal_ordered()

# Chemistry convention: requires a two-body, number-conserving operator.
chemist = chemist_ordered(ordered + FermionOperator("2^ 3^ 1 0"))
```

`normal_ordered(operator, hbar=1.0)` supports `FermionOperator`,
`BosonOperator`, `QuadOperator`, and `InteractionOperator`. Fermion and boson
reordering can recursively generate contraction terms and is exponential in
ladder-term locality. `chemist_ordered` is not a generic reorderer: it raises
for operators that are not two-body number-conserving. `reorder(operator,
order_function, num_modes=None, reverse=False)` remaps mode indices; its
`order_function(mode_idx, num_modes)` must be defined for every mode.

`count_qubits(operator)` returns the minimum occupied mode/qubit count. It is
`0` for a constant-only or zero symbolic operator, and for a
`MajoranaOperator` it converts the largest Majorana index into the number of
fermionic modes (`max_index // 2 + 1`, accounting for odd indices). It also
accepts `PolynomialTensor`, `InteractionOperator`, and selected diagonal/Ising
representations. It does not reserve a desired padded Hilbert space.

For algebraic utilities, `commutator(a, b)` computes `a*b - b*a` and
`anticommutator(a, b)` computes `a*b + b*a`; the operand Python types must match.
`double_commutator(op1, op2, op3, ...)` is an optimization-aware fermion/boson
helper and otherwise falls back to normal-ordered products. `bch_expand(*ops,
order=6)` returns a truncated `log(exp(x1)...exp(xN))`; it needs at least two
same-type operands, and `order` must be a non-negative integer. BCH order is a
formal truncation, not an exact exponential or convergence certificate.

## Tensor-backed representations

`PolynomialTensor(n_body_tensors)` stores arrays under action-bit keys. A key
such as `(1, 0)` represents coefficients of `a_p^ a_q`; `(1, 1, 0, 0)`
represents `a_p^ a_q^ a_r a_s`. The empty key `()` stores a scalar constant.
Each nonconstant tensor is square with side length `n_qubits`; `n_qubits` is
inferred from a nonconstant tensor. Element access translates operator-like
pairs into the tensor key and indices:

```python
import numpy
from openfermion import PolynomialTensor

t = PolynomialTensor({
    (): 0.25,
    (1, 0): numpy.zeros((2, 2), dtype=complex),
})
t[(0, 1), (1, 0)] = 0.5
assert t[(0, 1), (1, 0)] == 0.5
```

`PolynomialTensor` supports tensorwise arithmetic, equality within the package
tolerance, iteration over nonzero operator-like terms, `with_function_applied_elementwise`,
`projected_n_body_tensors(selection, exact=False)`, and
`rotate_basis(rotation_matrix, transpose=None)`. Set `transpose` explicitly:
`None` currently behaves like `True` but emits a `FutureWarning` and is slated
to change. `rotate_basis` mutates the tensor and returns `None`; the rotation
matrix is assumed to have compatible dimensions.

`InteractionOperator(constant, one_body_tensor, two_body_tensor)` is a
specialized `PolynomialTensor` with fixed keys `()`, `(1, 0)`, and
`(1, 1, 0, 0)`. Its convention is

```text
constant + sum[p,q] h[p,q] a_p^ a_q
          + sum[p,q,r,s] h[p,q,r,s] a_p^ a_q^ a_r a_s
```

Use `.one_body_tensor`, `.two_body_tensor`, `[(p,1),(q,0)]`,
`[(p,1),(q,1),(r,0),(s,0)]`, `.unique_iter(complex_valued=False)`,
`.projected(indices, exact=False)`, and `InteractionOperator.zero(n_qubits)`.
The specialized class is intended for Hermitian, number-conserving interaction
Hamiltonians; use `FermionOperator` for arbitrary polynomials. Chemistry
integral construction and file/model loading are intentionally routed away.

## Sparse conversion boundary

```python
from openfermion.linalg import get_sparse_operator

matrix = get_sparse_operator(mapped_qubit_operator, n_qubits=4)
assert matrix.shape == (16, 16)
```

`get_sparse_operator(operator, n_qubits=None, trunc=None, hbar=1.0)` accepts
`FermionOperator`, `QubitOperator`, `DiagonalCoulombHamiltonian`,
`PolynomialTensor`, `BosonOperator`, and `QuadOperator`. Fermionic non-qubit
inputs are JW-mapped internally. For `FermionOperator`, `n_qubits` pads the
matrix and must not be below `count_qubits`; for `QubitOperator`, the same
argument fixes the matrix dimension. Boson/quad inputs need a finite `trunc`
per mode. The result is a SciPy CSC sparse matrix. This boundary should remain
small and explicit; do not use it as a substitute for large solver or RDM
workflows.
