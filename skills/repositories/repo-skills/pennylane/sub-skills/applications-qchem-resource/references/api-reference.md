# Application modules API reference

## qchem

Verified signatures:

```python
qp.qchem.Molecule(symbols, coordinates, charge=0, mult=1,
                  basis_name="sto-3g", name="molecule", load_data=False,
                  l=None, alpha=None, coeff=None, normalize=True, unit="bohr")

qp.qchem.molecular_hamiltonian(molecule, method="dhf", active_electrons=None,
                               active_orbitals=None, mapping="jordan_wigner",
                               outpath=".", wires=None, args=None,
                               convert_tol=1e12)
```

Other qchem surfaces include `taper`, `symmetry_generators`, `paulix_ops`, `taper_operation`, `import_operator`, `from_openfermion`, and `to_openfermion`.

## Fermionic, bosonic, and spin mappings

Top-level exports include:

- Fermionic: `FermiC`, `FermiA`, `FermiWord`, `FermiSentence`, `jordan_wigner`, `parity_transform`, `bravyi_kitaev`.
- Bosonic: `BoseWord`, `BoseSentence`, `binary_mapping`, `unary_mapping`, `christiansen_mapping`.
- Spin: use `qp.spin` for spin Hamiltonian helpers and lattices.

Use the operators/transforms sub-skill after mapping to qubit operators.

## Resource and estimator

Verified signatures:

```python
qp.specs(qnode, level=None, compute_depth=None)

qp.estimator.estimate(workflow, gate_set=None, zeroed_wires=0,
                      any_state_wires=0, tight_wires_budget=False,
                      config=None)
```

`qp.specs` returns a callable that reports circuit specifications for given QNode inputs. The estimator accepts workflows, resource operators, resources objects, or QNodes and returns resource estimates or a callable that produces them.

## QAOA, kernels, and qcut

- `qp.qaoa` contains layers and helpers for QAOA-style workflows.
- `qp.kernels` contains cost functions, utility functions, and postprocessing for quantum kernels.
- `qp.qcut.cut_circuit` and `qp.qcut.cut_circuit_mc` route to circuit-cutting workflows.

These can involve optional solvers or graph partitioners. Verify dependencies for nontrivial cases.

## Noise, shadows, pulse, FTQC, and lie algebra

Some advanced modules overlap with core circuits:

- `qp.shadows.ClassicalShadow` and shadow measurements support classical shadow workflows.
- `qp.pulse.ParametrizedHamiltonian(coeffs, observables)` is the verified pulse signature.
- `qp.ftqc` and `qp.liealg` are specialized; treat them as advanced/experimental or restricted unless the task names their APIs directly.

## Optional dependency policy

Do not install or claim all optional dependencies. Map the requested workflow first:

- Qchem external solvers/conversions: may require OpenFermion/PySCF and related chemistry packages.
- Kernels: may require CVX packages for some workflows.
- Qcut: may require KAHYPAR/opt_einsum for partitioning/optimization workflows.
- I/O adjacent applications: may require Qiskit, PyQuil, OpenQASM3, Qualtran, Stim, PyZX, or Quimb.
- Hardware scale: may require external simulators or plugins.
