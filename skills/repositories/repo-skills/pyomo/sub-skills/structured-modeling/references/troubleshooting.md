# Structured Modeling Troubleshooting

## Purpose

Read this when a GDP, DAE, network, MPEC, or units-based model misbehaves.

## Common failures

### GDP model solves before transformation

Symptoms:

- The model looks correct, but the solver cannot process it directly.

Likely causes:

- The GDP reformulation step was omitted.
- The wrong transformation name was used.

Recovery:

- Apply the chosen GDP transformation before solving.
- Verify the transform name in the reference file.

### DAE model is not ready to solve

Symptoms:

- The model still contains a `ContinuousSet` or other continuous structure.

Likely causes:

- The discretization step was skipped.
- `wrt`, `nfe`, or `ncp` was not set correctly.

Recovery:

- Discretize before solving.
- Keep the discretization call adjacent to the model in the example.

### Network model has no solver-ready constraints

Symptoms:

- A port/arc model builds, but the solver sees too little structure.

Likely causes:

- `network.expand_arcs` was not applied.
- The ports do not use compatible rules.

Recovery:

- Expand arcs before solving or sequential decomposition.
- Check `Port.Equality` versus `Port.Extensive` where the flows matter.

### Units check fails

Symptoms:

- A units-consistency helper raises an exception.

Likely causes:

- Expressions mix incompatible dimensions.
- Offset temperature units were used inside arithmetic expressions.

Recovery:

- Check units on the affected expression or component.
- Convert to compatible absolute units before combining values.

## Next step

If the issue is actually solver backend availability or GUI dependency setup,
move to `solver-extensions`.
