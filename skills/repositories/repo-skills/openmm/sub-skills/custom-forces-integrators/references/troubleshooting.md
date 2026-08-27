# Troubleshooting Custom Forces and Integrators

Use this guide to diagnose OpenMM custom expressions, parameter updates, force groups, and custom integrator algorithms.

## Expression and Variable Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Parse error when creating a `Context` | Unsupported operator/function, mismatched parentheses, typo in semicolon definitions | Reduce the expression to a tiny case; use only OpenMM-supported algebra and functions; add intermediate terms one at a time. |
| `Unknown variable` or similar exception | Expression references a parameter, coordinate, distance, CV, or integrator variable not defined for that class | Check class-specific variables: `r` for pair distances, `theta` for angle/torsion, `x/y/z` for external, `name1/name2` for custom nonbonded per-particle parameters. |
| Correct expression gives wrong sign/magnitude | Unit mismatch or unintended OpenMM internal unit conversion | Pass `openmm.unit` quantities from Python; verify a single hand-computed configuration on `Reference`. |
| Intermediate value not recognized | Semicolon definition order is wrong | In OpenMM expressions, use the intermediate in the main expression first, then define it after `;`; dependencies must also appear before their definitions. |
| Different results after particle order changes | `CustomNonbondedForce` expression is not symmetric | Replace asymmetric terms such as `sigma1-sigma2` with symmetric mixing rules. |

## Counts, Topology, and Context Creation

- `CustomNonbondedForce` must have exactly one `addParticle()` record per `System` particle. Too few or too many records fail at `Context` creation.
- Bond, angle, torsion, donor/acceptor, group, and centroid records must use valid particle indices and the correct number of per-record parameters.
- Adding particles, adding interaction records, adding a new force, changing the expression, changing the number of parameters, or changing tabulated function dimensionality after context creation requires a new `Context` or `context.reinitialize()`.
- Changing only global parameter values should use `context.setParameter()`.
- Changing only existing per-element parameter values should use the force's setter followed by `force.updateParametersInContext(context)` if the class supports it.

## Parameter Updates

- If changing a global has no effect, confirm the parameter name exactly matches the name declared by the force and the `Context` being used.
- If changing per-particle/per-bond parameters has no effect, make sure `updateParametersInContext(context)` is called on the same force object that is already in the system.
- If `updateParametersInContext()` raises or leaves stale values, check whether the attempted change modifies counts, ordering, exclusions, groups, cutoffs, or other structural data; those changes need reinitialization.
- For `CustomCVForce`, updates to inner force parameters may need the inner context returned by `CustomCVForce.getInnerContext(context)` when updating the force used as a collective variable.
- For `CustomNonbondedForce` with long-range correction, frequent global or per-particle updates can be unexpectedly slow because the correction is recomputed.

## Exclusions, Cutoffs, and Periodicity

- Double-counted `CustomNonbondedForce` energy often comes from overlapping interaction groups. A pair that appears in two groups is evaluated twice.
- Missing energy often comes from an exclusion, an interaction group that omits the pair, a cutoff distance too small for the test geometry, or missing periodic box vectors.
- With `CutoffPeriodic`, set valid periodic box vectors before evaluating the context. The cutoff should be compatible with the box size.
- Switching distance must be less than the cutoff distance.
- Long-range correction is best for slowly changing periodic nonbonded parameters, especially constant-pressure simulations; it is usually wrong for unsupported expressions and costly for frequently changing parameters.

## Force Groups and Energy Queries

- Force groups are numbered 0 through 31. All forces start in group 0 unless explicitly changed.
- `Context.getState(getEnergy=True, groups={0, 2})` accepts a set of group indices; `groups=-1` evaluates all groups. A tuple such as `(0, 2)` is not valid.
- If a query-only force changes the dynamics, call `integrator.setIntegrationForceGroups(mask)` to integrate only the intended groups and query the monitor force separately.
- For `CustomIntegrator`, do not combine multiple `fN` or multiple `energyN` variables in one computation expression. Split the calculation into separate computation steps.
- In MTS integrators, group frequencies must form integer multiples after sorting. Invalid ratios raise `ValueError` or produce an invalid algorithm.

## CustomIntegrator Failures

- NaN positions or velocities after one step usually indicate an unstable time step, zero/incorrect masses, division by zero in an expression, missing constraints, or an unbounded custom force.
- Constraints drifting means the integrator is missing `addConstrainPositions()`, `addConstrainVelocities()`, or the velocity correction based on constrained displacement.
- Barostats/thermostats not acting can mean the algorithm omitted `addUpdateContextState()`.
- Infinite hangs can come from `beginWhileBlock()` conditions that never become false. Add a counter and assert it decreases.
- Stochastic trajectories are not guaranteed to match exactly across platforms. Validate seeded behavior only on the same platform and use statistical checks for portability.
- If kinetic energy reporting is wrong for leapfrog-like algorithms, provide a `setKineticEnergyExpression()` that matches the algorithm's on-step velocity.

## Serialization and Portability

- Use `XmlSerializer.serialize(system)` and `XmlSerializer.deserialize(xml)` for custom systems and forces that need portable definitions.
- Serialize custom integrators separately when the algorithm is part of the reproducible setup.
- After deserialization, build a tiny `Reference` context and assert finite energy/forces; XML round trips preserve definitions but do not prove the expression is physically correct.
- Avoid relying on Python-side helper closures or original script files at runtime. Put all required expressions, parameters, and tabulated values in the serialized objects or bundled scripts.

## Minimal Debug Procedure

1. Run `scripts/custom_force_smoke.py` to ensure the installed OpenMM package and `Reference` platform are usable.
2. Rebuild the failing force in a two- to four-particle `System` with explicit positions and no unrelated forces.
3. Query total energy and per-group energy, then compare against a manual calculation.
4. Change one global with `Context.setParameter()` and re-query energy.
5. Change one per-element parameter, call `updateParametersInContext()`, and re-query energy.
6. If using nonbonded terms, list exclusions and interaction groups and manually enumerate expected pairs.
7. Serialize, deserialize, and repeat the finite-energy check before embedding the system into a full simulation workflow.
