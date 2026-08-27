---
name: analysis-and-measurements
description: "Use OpenFermion for bounded sparse or dense operator analysis,
  Davidson and eigensolver workflows, RDM reconstruction and mapping,
  symmetry-sector restriction, measurement grouping and partitioning, VPE
  estimation, resource functionals, and grid or lattice numerical helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Analysis and measurements

Use this route when the task is to **analyze an already constructed public
OpenFermion operator or numerical tensor**: obtain a sparse matrix, compute a
small spectrum or ground state, restrict a Jordan–Wigner operator to a symmetry
sector, map or validate RDMs, group compatible measurements, estimate a VPE
functional, or use grid/lattice indexing helpers.

## Route first

- Operator construction, fermion-to-qubit transforms, or choosing a mapping:
  route to [operators-and-transforms](../operators-and-transforms/SKILL.md).
- Molecular, Hubbard, jellium, or other model construction: route to
  [hamiltonians-and-chemistry](../hamiltonians-and-chemistry/SKILL.md).
- Circuit synthesis, VPE circuit creation, or state simulation: route to
  [circuits-and-simulation](../circuits-and-simulation/SKILL.md). This skill
  only processes bounded numerical or measurement data for those workflows.
- Large benchmarks, performance claims, multiprocessing experiments, and
  production integrations are evidence only; do not infer scalability from a
  tiny smoke check.

Read [references/api-reference.md](references/api-reference.md) for signatures,
shape conventions, and public import locations. Read
[references/workflows.md](references/workflows.md) before doing a numerical
workflow. Use [references/troubleshooting.md](references/troubleshooting.md)
when an import, dimension, backend, tensor, or solver check fails.

## Guardrails before numerical work

1. Identify the operator family (`QubitOperator`, `FermionOperator`, bosonic
   operator, polynomial tensor, or an existing sparse/linear operator), the
   qubit/mode count, and whether the operator is Hermitian.
2. For a qubit Hilbert space, require the matrix dimension to be exactly
   `2**n_qubits`; reject an underspecified `n_qubits` rather than silently
   truncating. For bosons, provide a positive integer `trunc` and estimate the
   dimension `trunc**n_modes` first.
3. Keep dense diagonalization bounded. `sparse_eigenspectrum` converts the
   entire matrix to dense form and is appropriate only for a deliberately tiny
   matrix. Prefer `get_ground_state`, `get_gap`, or Davidson for larger but
   still bounded sparse cases.
4. Check state shape and normalization before `expectation` or `variance`.
   These functions do not repair a wrong basis, wrong dimension, or an
   unnormalized state.
5. For RDMs, state the number of spin-orbitals, particle number, and exact
   tensor convention before converting. Reject incompatible ranks or leading
   dimensions before calling an einsum or reconstruction routine.

## Main routes

- **Sparse matrix and spectrum:** use `get_sparse_operator`; inspect
  `.shape`, `.format`, and `.nnz`; use `get_ground_state` for the lowest state,
  `get_gap` for a Hermitian gap, and `sparse_eigenspectrum` only after a dense
  memory bound. The bundled
  [sparse analysis smoke helper](scripts/sparse_analysis_smoke.py) is a safe
  tiny example and prints the matrix shape and ground energy.
- **Symmetry-sector analysis:** use `jw_number_restrict_operator` or
  `jw_sz_restrict_operator` on a Jordan–Wigner sparse matrix, or use
  `get_number_preserving_sparse_operator` when constructing a fermionic matrix
  directly in a bounded sector. Restricted state vectors are generally not
  normalized; renormalize before interpreting expectations.
- **Davidson:** use `SparseDavidson` for a sparse matrix and `QubitDavidson`
  for a `QubitOperator` without materializing its full matrix. Supply a
  diagonal, a dimension-compatible initial guess, and bounded
  `DavidsonOptions`; inspect the returned `success` flag and residual rather
  than assuming convergence.
- **RDMs and equality constraints:** use the mapping functions only with the
  documented OpenFermion index order. `get_interaction_rdm` reconstructs an
  `InteractionRDM` from measured qubit-term coefficients and can be
  O(`n_qubits**4`); specify `n_qubits` when identity or trailing orbitals make
  counting ambiguous. Equality projection is a resource-functional workflow,
  not a generic RDM repair operation.
- **Measurement grouping and partitioning:** use tensor-product basis grouping
  for a `QubitOperator`; use qubit partition iterators for coverage families;
  use fermion/Majorana pairings only when their combinatorial output is the
  requested measurement schedule. They do not synthesize circuits or estimate
  shot noise.
- **VPE and resource functionals:** `PhaseFitEstimator` requires known
  eigenvalues and phase samples aligned to its simulation points. The one-norm
  functions consume spatial-orbital integral tensors and distinguish inclusion
  of the constant. `is_contextual` is imported from
  `openfermion.functionals.contextuality`, not the root package.
- **Grid and lattice helpers:** use `Grid` for centered real-space and
  reciprocal-space indexing, and `HubbardSquareLattice` for site, degree of
  freedom, spin, and neighbor iteration. These helpers do not construct a
  Hamiltonian; route model construction elsewhere.

## Completion checklist

- Record input type, `n_qubits`/mode count, truncation or sector, matrix shape,
  Hermiticity check, solver path, tolerance/iteration bound, and numerical
  result.
- For spectra, state whether the result was dense or iterative and give the
  expected dimension. For RDMs, record ranks, shapes, particle/hole counts,
  contraction identity, and round-trip or trace checks.
- For measurements, record the partition/grouping convention and whether
  identity terms or unpaired labels are present.
- Stop and diagnose shape, basis, backend, or convergence failures using the
  troubleshooting table; do not increase dimensions or iteration limits
  blindly.
