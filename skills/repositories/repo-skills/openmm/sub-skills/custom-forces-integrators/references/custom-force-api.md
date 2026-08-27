# Custom Force API Reference

This reference covers OpenMM custom expression forces and the update/validation patterns that keep hand-built systems correct and serializable.

## Pick the Force Class

| Need | Use | Expression variables and records |
| --- | --- | --- |
| Pair-specific bonded distance | `CustomBondForce` | Energy depends on `r`; add per-bond parameters and `addBond(p1, p2, params)`. |
| Three-particle angle | `CustomAngleForce` | Energy depends on `theta`; add per-angle parameters and `addAngle(p1, p2, p3, params)`. |
| Four-particle dihedral | `CustomTorsionForce` | Energy depends on `theta` in `[-pi, pi]`; add per-torsion parameters and `addTorsion(...)`. |
| Particle position restraint or field | `CustomExternalForce` | Energy depends on `x`, `y`, `z`; add one record per affected particle. |
| Arbitrary bonded geometry over N particles | `CustomCompoundBondForce` | Energy can use declared distances, angles, dihedrals, and particle coordinates. |
| Center-of-mass/group restraints | `CustomCentroidBondForce` | Define weighted groups, then bonds between group centroids. |
| Pairwise nonbonded custom term | `CustomNonbondedForce` | Energy depends on `r`; per-particle parameters appear as `name1` and `name2`; expression must be symmetric. |
| Non-pairwise nonbonded term | `CustomManyParticleForce` | Energy over N particles; control permutations and type filters. |
| Generalized Born or staged scalar calculations | `CustomGBForce` | Add computed values before energy terms; platform support is stricter for computed-value ordering. |
| Donor/acceptor hydrogen bond expression | `CustomHbondForce` | Energy uses donor/acceptor group distances, angles, and dihedrals; supports exclusions. |
| Collective variable bias | `CustomCVForce` | Add scalar `Force` objects as CVs; outer expression depends on CV names and globals. |
| Volume-only energy | `CustomVolumeForce` | Energy depends on periodic box vectors and affects volume-dependent thermodynamics, not particle forces. |

## Expression Syntax

- Operators: `+`, `-`, `*`, `/`, `^`, and parentheses.
- Functions: `sqrt`, `exp`, `log`, trigonometric and hyperbolic functions, `erf`, `erfc`, `min`, `max`, `abs`, `floor`, `ceil`, `step`, `delta`, and `select`.
- `step(x)` is 0 for `x < 0` and 1 otherwise; `delta(x)` is 1 only when `x` is exactly 0; `select(x, y, z)` returns `z` when `x` is 0 and `y` otherwise.
- Intermediate definitions follow the main expression after semicolons, for example `k*(r-r0)^2; r0=0.5*(r01+r02)`. A symbol must be used before the semicolon definition that defines it.
- Distances and energies are interpreted in OpenMM's internal unit system. In Python, pass `openmm.unit` quantities when setting parameters and positions to avoid silent scale mistakes.

## Parameters and Updates

- Global parameters are declared with `addGlobalParameter(name, default)` and are stored in the `Context`. Change them cheaply with `context.setParameter(name, value)`.
- Multiple custom forces can share the same global parameter by using the same name; one `Context.setParameter()` then changes all forces that depend on it.
- Per-element parameters are part of the `Force` definition. After `Context` creation, changes via `setParticleParameters()`, `setBondParameters()`, `setAngleParameters()`, and similar setters do nothing until `updateParametersInContext(context)` is called.
- `updateParametersInContext()` is more expensive than `Context.setParameter()` but usually much cheaper than `context.reinitialize()`. Use `reinitialize()` only when changing counts, adding/removing forces, changing topology, or altering unsupported structural features.
- `CustomNonbondedForce` long-range correction requires expensive precomputation and is recomputed when globals change or per-particle parameters are updated; disable it for rapidly varying alchemical or adaptive parameters unless the correction is required.
- Request derivatives with `addEnergyParameterDerivative(global_name)` after declaring the global parameter, then query them with `context.getState(getParameterDerivatives=True)` or use derivative variables in `CustomIntegrator` expressions.

## Nonbonded Details

- Add exactly one `CustomNonbondedForce.addParticle(params)` record for every particle in the `System` before creating a `Context`.
- Use symmetric expressions. `sigma1+sigma2`, `sqrt(epsilon1*epsilon2)`, and `abs(charge1-charge2)` are symmetric; `sigma1-sigma2` is not.
- Use `addExclusion(i, j)` to omit bonded or otherwise excluded pairs. Exclusions still apply inside interaction groups.
- Use `addInteractionGroup(set1, set2)` to restrict evaluation to selected cross interactions. If a particle pair appears in multiple groups, OpenMM evaluates it multiple times; this can be intentional, but it is a common double-counting bug.
- For cutoffs, set the nonbonded method (`NoCutoff`, `CutoffNonPeriodic`, or `CutoffPeriodic`) and cutoff distance. If using a switching function, enable it and set a switching distance strictly less than the cutoff.
- Periodic custom nonbonded systems need valid periodic box vectors before context creation.

## Tabulated Functions

- `CustomNonbondedForce`, `CustomGBForce`, `CustomHbondForce`, `CustomCompoundBondForce`, `CustomCentroidBondForce`, `CustomCVForce`, and `CustomIntegrator` can use `addTabulatedFunction()` where supported.
- Choose continuous functions (`Continuous1DFunction`, `Continuous2DFunction`, `Continuous3DFunction`) for interpolated profiles and discrete functions for indexed lookup tables.
- After editing function values with `setFunctionParameters()`, call the owning force's `updateParametersInContext(context)` when a context already exists.
- Keep tabulated function names unique within the force/integrator and avoid reusing names that collide with variables, parameters, or intermediate definitions.

## Force Groups and Serialization

- Every `Force` defaults to group 0. Assign groups with `force.setForceGroup(group)` where `group` is 0 through 31.
- Query subsets with `context.getState(getEnergy=True, groups={0, 2})` or a bit mask such as `(1 << 0) | (1 << 2)`. `groups=-1` means all groups.
- Exclude groups from dynamics with `integrator.setIntegrationForceGroups(mask)` when a force is query-only, such as a restraint monitor or analysis CV.
- Serialize custom systems with `XmlSerializer.serialize(system)` and `XmlSerializer.serialize(integrator)`; custom expressions, parameters, force groups, tabulated functions, and many custom integrator variables are part of the serialized object.
- Always deserialize and evaluate a small `Reference` platform context when portability matters, because serialization catches only structural preservation, not expression correctness.
