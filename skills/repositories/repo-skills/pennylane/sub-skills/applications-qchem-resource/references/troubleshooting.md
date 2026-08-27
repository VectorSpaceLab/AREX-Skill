# Application module troubleshooting

## Qchem optional dependency failures

- Base PennyLane can construct some qchem objects, but molecular Hamiltonian generation and conversions may require optional chemistry packages.
- Confirm units (`bohr` vs `angstrom`), charge, multiplicity, active space, and basis before blaming dependencies.
- Use tiny molecules such as H2 for smoke checks.
- Avoid network or external solver workflows unless the user explicitly approved them.

## Large scientific workflows are slow

- Resource estimation, qchem, qcut, and kernel workflows can grow exponentially or require heavy linear algebra.
- Start with the smallest molecule/circuit/wire count and then scale.
- State when a result is a smoke check rather than a production scientific benchmark.

## Mapping surprises

- Fermionic/bosonic/spin mappings can produce qubit operators with wire/order conventions that matter downstream.
- After mapping, inspect with `qp.simplify`, `qp.matrix(..., wire_order=...)`, and operator equality helpers.
- For tapering and symmetry workflows, record the chosen symmetries and active space.

## Resource estimate mismatch

- `qp.specs` reports circuit-level specs at the selected transform level.
- `qp.estimator.estimate` can use a different resource model/gate set.
- Specify whether the task wants user-level gate counts, device-expanded gates, gradient-level resources, or hardware-target resources.

## qcut/kernels optional solvers

- KAHYPAR, CVX solvers, and `opt_einsum` are optional surfaces. Install only the one needed by the selected workflow.
- If a graph partitioner is missing, either choose a deterministic manual cut for a tiny example or mark the partitioning feature unverified.

## Hardware and plugin scale

- Application workflows can run on `default.qubit` for tiny CPU checks, but scale or production speed may require Lightning or external plugins.
- GPU plugin success requires a verified plugin package, accelerator wheel, driver, and visible hardware.
- Do not report CPU smoke success as GPU readiness.

## Experimental or restricted modules

- Treat `pennylane.ftqc`, `pennylane.labs`, and specialized advanced modules carefully. Check source/tests and module-boundary rules before editing them.
- If public docs are sparse, state the uncertainty and use installed signature inspection before proposing code.
