# Operators, templates, and transforms API reference

## Operation examples and signatures

Verified examples:

```python
qp.RX(phi, wires)
qp.RY(phi, wires)
qp.RZ(phi, wires)
qp.Rot(phi, theta, omega, wires)
qp.CNOT(wires)
qp.Hadamard(wires)
qp.PauliX(wires)
qp.PauliY(wires)
qp.PauliZ(wires)
```

Wires accept a `Wires` object, iterable of hashable labels, or a single hashable label.

## Template signatures verified

```python
qp.AmplitudeEmbedding(features, wires, *, pad_with=None, normalize=False, validate_norm=True)
qp.AngleEmbedding(features, wires, rotation="X")
qp.StronglyEntanglingLayers(weights, wires, ranges=None, imprimitive=qp.CNOT)
qp.BasisState(state, wires)
qp.StatePrep(state, wires, pad_with=None, normalize=False, validate_norm=False)
qp.QFT(wires)
qp.GroverOperator(wires, work_wires=())
qp.QuantumPhaseEstimation(unitary, target_wires=None, estimation_wires=None)
```

Always check template shape helpers or docstrings for production code. Typical failures are wrong rank, wrong number of wires, unnormalized amplitudes, or non-differentiable preprocessing.

## Operator arithmetic and inspection

Common helpers:

- Composition: `qp.sum`, `qp.prod`, `qp.s_prod`, `qp.pow`, `qp.adjoint`, `qp.ctrl`, `qp.cond`, `qp.exp`, `qp.dot`.
- Equality/validation: `qp.equal`, `qp.assert_equal`, `pennylane.ops.functions.assert_valid`.
- Inspection: `qp.matrix(op, wire_order=None)`, `qp.eigvals(op, k=1, which="SA")`, `qp.generator`, `qp.is_unitary`, `qp.is_hermitian`, `qp.is_commuting`.
- Rewriting: `qp.simplify(input)`, `qp.map_wires(input, wire_map, queue=False, replace=False)`.
- Pauli tools: `qp.pauli_decompose`, `qp.pauli` module classes/utilities.

Use `wire_order` when matrix layout matters. Otherwise multi-wire matrices can appear correct but be ordered differently from downstream code.

## Transform API

```python
qp.transform(tape_transform=None, pass_name=None, *, setup_inputs=None,
             expand_transform=None, classical_cotransform=None,
             is_informative=False, final_transform=False,
             use_argnum_in_expand=False)
```

Packaged transform examples:

```python
qp.compile(tape, pipeline=(...), basis_set=None, num_passes=1)
qp.decompose(tape, *, gate_set=None, stopping_condition=None,
             max_expansion=None, num_work_wires=0,
             minimize_work_wires=False, fixed_decomps=None,
             alt_decomps=None, strict=True)
```

Most transforms can be used as decorators around QNodes or quantum functions, but many underlying functions operate on tapes and return `(tapes, processing_fn)`. When a user sees such a pair, they are at transform-internal level.

## Decomposition and gate-set utilities

- `pennylane.decomposition.add_decomps`, `list_decomps`, `inspect_decomps`, and `gate_sets` manage decomposition rule availability.
- `resource_rep` and resource-aware decomposition utilities are useful when resource estimation is the goal; route heavy resource tasks to the application/resource sub-skill.

## Custom operator requirements

For source or user-defined custom operations:

- Inherit from `qp.operation.Operation` or another appropriate `Operator` subclass.
- Parameters are positional; wires are supplied with `wires=...`.
- Hyperparameters belong in `self._hyperparameters`.
- Static decomposition functions use the `compute_decomposition(*parameters, wires, **hyperparameters)` pattern.
- Define `_unflatten` if the constructor does not match the default flatten/unflatten contract.
- Validate with `assert_valid(op)` and add focused tests.
