---
name: openfermion
description: "Guide OpenFermion workflows for fermionic and qubit operator
  algebra, Hamiltonian construction, quantum-chemistry data, circuit synthesis,
  sparse analysis, measurements, and resource-oriented utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenFermion

Use this skill when a task names OpenFermion or asks for Python workflows around
fermionic systems, second quantization, qubit Hamiltonians, quantum chemistry,
Jordan–Wigner/Bravyi–Kitaev mappings, Trotter/UCC circuits, RDMs, measurement
grouping, or sparse operator analysis.

## Fast route

1. **Install and smoke-check.** Install the public `openfermion` distribution in
   Python >=3.10, then run `python -c "import openfermion; print(openfermion.__version__)"`.
   The package uses Cirq core, NumPy, SciPy, SymPy, HDF5, and related runtime
   dependencies. See [troubleshooting](references/troubleshooting.md) for
   optional extras and import failures.
2. **Select the owning route.** Use the focused sub-skill that matches the
   user's artifact, not the source package directory name:
   - [operators-and-transforms](sub-skills/operators-and-transforms/SKILL.md)
     for symbolic operators, normal ordering, and fermion-to-qubit mappings.
   - [hamiltonians-and-chemistry](sub-skills/hamiltonians-and-chemistry/SKILL.md)
     for Hubbard/jellium/model Hamiltonians and molecular metadata or tensors.
   - [circuits-and-simulation](sub-skills/circuits-and-simulation/SKILL.md) for
     Trotter, UCC, Slater/Gaussian preparation, Cirq circuits, and VPE circuits.
   - [analysis-and-measurements](sub-skills/analysis-and-measurements/SKILL.md)
     for sparse matrices, eigensolvers, RDMs, measurement grouping, and
     resource functionals.
3. **Record the contract before computing.** Preserve operator family, mode or
   qubit ordering, coefficient units, tensor shapes, `n_qubits`, boundary or
   particle-number choices, optional dependency state, and the expected output.
4. **Keep numerical work bounded.** Construct tiny fixtures first; validate
   dimensions and Hermiticity before matrix conversion, dense diagonalization,
   RDM contraction, or circuit expansion. Do not infer scalability from a
   smoke test.
5. **Handoff across routes explicitly.** A model builder supplies an operator
   contract to the mapping route; a mapping supplies a qubit operator to the
   circuit or analysis route; analysis returns shapes, convergence signals, and
   numerical results. Do not silently choose conventions at a boundary.

## Public package boundary

OpenFermion is primarily a Python library, not a package-specific command-line
application. Install external simulators, electronic-structure packages, or
hardware plugins separately. The optional `resources` extra adds PySCF, JAX,
JAXlib, and ASE for selected resource-estimation workflows; it is not required
for core operator, transform, Hamiltonian, circuit, or sparse-analysis usage.
PubChem lookup is network-dependent even though the base distribution includes
its client library. Never claim that `MolecularData` metadata is a completed
quantum-chemistry calculation.

For verified signatures and return-shape notes, read
[api-index.md](references/api-index.md). For cross-cutting install, optional
package, file, network, and numerical failures, read
[troubleshooting.md](references/troubleshooting.md). Run
[scripts/check_openfermion.py](scripts/check_openfermion.py) for a safe public
import and capability diagnostic; it performs no network access or file writes.
Read [repo-provenance.md](references/repo-provenance.md) before deciding whether
this skill is stale for a particular OpenFermion checkout.

## Self-contained smoke helpers

Each route owns a tiny helper that is independent of the original checkout:

- `operators-and-transforms/scripts/smoke_transform.py` maps a two-mode hopping
  term and can report a sparse shape.
- `hamiltonians-and-chemistry/scripts/build_tiny_hamiltonian.py` emits a small
  Hubbard or molecular-metadata summary without writing files.
- `circuits-and-simulation/scripts/circuit_smoke.py` reports a bounded Cirq
  circuit and optional Slater preparation.
- `analysis-and-measurements/scripts/sparse_analysis_smoke.py` converts a tiny
  qubit operator and checks a ground-state residual.

Use `--help` first and keep all input dimensions within the helper's documented
bounds. These are structural checks, not scientific benchmarks.
