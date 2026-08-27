# Cross-cutting troubleshooting

Read this reference when a workflow fails before the focused sub-skill's
specialized diagnosis.

## Install and import

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: openfermion` | The active Python is not the environment where the distribution was installed | Run `python -m pip show openfermion`, install with that same `python -m pip`, then rerun `python -c "import openfermion"`. Do not rely on shell activation state. |
| Import fails inside `cirq` or `scipy` | Dependency variant is missing or incompatible | Use a clean Python >=3.10 environment and the public `openfermion` install; inspect `python -m pip check`. Install the optional `resources` extra only for resource-estimation APIs. |
| Optional resource import fails | PySCF, JAX/JAXlib, or ASE is absent or incompatible | Treat the capability as optional. Install `openfermion[resources]` or the documented package separately, then verify the exact submodule. Do not claim core OpenFermion is broken. |
| An external plugin is unavailable | FQE, PySCF, Psi4, or a simulator plugin is separate from the core package | Preserve the operator/model contract and stop at the plugin boundary. Install and verify the plugin in its own environment before using it. |

## Input, convention, and API errors

- **Term syntax:** fermionic and bosonic terms are tuples of `(mode, action)`;
  `1` is creation and `0` annihilation. Qubit terms use `(index, "X"|"Y"|"Z")`.
  Validate integers, action values, and mode ordering before transforming.
- **Operator family mismatch:** a `FermionOperator`, `QubitOperator`,
  `InteractionOperator`, and `PolynomialTensor` do not share every method.
  Record the family, then route conversion or mapping to the operators route.
- **Underspecified dimensions:** `count_qubits` only reflects indices present.
  Pass an explicit `n_qubits` when trailing orbitals or padded Hilbert spaces
  matter. Never use a smaller value than the required mode count.
- **Unexpected output terms:** compare `terms`, `compress()`, `isclose()`,
  Hermiticity, spectra, or sparse matrices under the same ordering and size;
  do not compare string formatting.
- **Cirq API mismatch:** inspect the installed Cirq version and use the helper's
  public API. OpenFermion does not promise compatibility with arbitrary plugin
  simulators or hardware devices.

## Data, files, and network

- `MolecularData` metadata is not an integral result. Calls such as
  `get_integrals()` or `get_molecular_hamiltonian()` can raise a missing-data
  error until a compatible chemistry calculation has populated the record.
- HDF5 loading/saving depends on valid filenames and permissions. Use a fresh
  explicit data location, avoid accidentally overwriting a record, and validate
  geometry, basis, multiplicity, and charge before writing.
- PubChem helpers require network access and may return no structure for an
  invalid identifier or unsupported structure type. Keep network access outside
  bounded smoke checks; record the request and returned structure explicitly.
- Cloud libraries, notebooks, and external datasets are evidence or inputs, not
  runtime dependencies of this skill. Replace them with a tiny fixture where a
  deterministic check is sufficient.

## Numerical and workload failures

- A qubit matrix has dimension `2**n_qubits`; a dense spectrum scales as the
  square of that dimension and is only suitable for tiny fixtures. Prefer sparse
  conversion plus a bounded iterative method.
- Before eigensolving, validate Hermiticity, sparse shape, state normalization,
  initial-guess shape, tolerances, and iteration bounds. If Davidson reports
  `success=False`, inspect residual and diagonal/preconditioner assumptions
  before raising limits.
- RDM and measurement functions have strict index order and tensor-rank
  contracts. Check particle number, spin-orbital count, leading dimensions,
  and trace/contraction identities before calling an einsum-heavy helper.
- Trotter, UCC, and state-preparation outputs can grow rapidly. Start with a
  two- or four-mode fixture, record formula order/step count, and preserve any
  final swap permutation before increasing the problem size.

## Safe recovery sequence

1. Reproduce the failure with the smallest input and the exact public import.
2. Print package version, operator family, dimensions, shapes, and optional
   dependency status; omit private environment paths from shared reports.
3. Consult the owning sub-skill reference and run its bundled tiny helper.
4. Change one convention or dependency at a time, retaining a before/after
   check such as `isclose`, matrix shape, norm, residual, trace, or circuit
   depth.
5. Stop when the failure requires credentials, network, a plugin, unavailable
   hardware, or a large/long workload; report that boundary instead of masking
   it as a core package result.
