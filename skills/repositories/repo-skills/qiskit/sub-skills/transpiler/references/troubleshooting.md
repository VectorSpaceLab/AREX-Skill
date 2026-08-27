# Transpiler troubleshooting

## Basis-gate or target mismatch

**Symptom**: `TranspilerError` or a target-related error says the circuit cannot be compiled.

**Cause**: the input circuit uses gates or qubit interactions that the backend target does not support.

**Fix**: check the backend's basis gates, coupling map, and target size before changing the pass manager.

## Layout or routing looks wrong

**Symptom**: the output circuit is valid but unexpectedly reordered, swapped, or decomposed.

**Cause**: the preset pipeline chose a different layout or routing method than you expected.

**Fix**: make the stage explicit, seed stochastic stages, and compare the output at multiple optimization levels.

## `CircuitTooWideForTarget`

**Symptom**: the circuit is wider than the selected backend or target.

**Cause**: the circuit needs more qubits than the backend exposes.

**Fix**: reduce the circuit width or choose a larger target before debugging the optimizer.

## Optional transpiler passes are missing

**Symptom**: a pass or stage cannot be enabled because an import failed.

**Cause**: the pass depends on an optional package such as `z3-solver` or `python-constraint`.

**Fix**: install the targeted extra instead of broadening the whole environment.

## Backend defaults override your expectations

**Symptom**: the same circuit compiles differently when a backend is provided versus a raw target or loose constraints.

**Cause**: the backend can supply stage defaults that change the pipeline.

**Fix**: check whether `ignore_backend_supplied_default_methods` or an explicit stage method is needed.

## Reproducibility is inconsistent

**Symptom**: two transpiles of the same circuit do not match exactly.

**Cause**: the pipeline uses seeded or heuristic stages that were not pinned.

**Fix**: set `seed_transpiler` and keep the environment stable while comparing results.
