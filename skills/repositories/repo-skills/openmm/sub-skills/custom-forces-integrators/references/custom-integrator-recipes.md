# CustomIntegrator Recipes

`CustomIntegrator` defines a time step as an ordered list of computations over persistent global variables and per-degree-of-freedom variables. It is the right tool for nonstandard deterministic or stochastic algorithms, MTS methods, alchemical parameter dynamics, and force-group-specific integration.

## Built-In Variables

| Variable | Type | Meaning |
| --- | --- | --- |
| `dt` | global | Current step size. |
| `energy` | global read-only | Total potential energy for integrated force groups. |
| `energy0`, `energy1`, ... | global read-only | Potential energy from one force group. A single computation may depend on only one energy variable. |
| `x` | per-DOF | Particle coordinates. |
| `v` | per-DOF | Particle velocities. |
| `f` | per-DOF read-only | Total force on each degree of freedom. |
| `f0`, `f1`, ... | per-DOF read-only | Force from one force group. A single computation may depend on only one force variable. |
| `m` | per-DOF read-only | Particle mass for each degree of freedom. Zero-mass particles are skipped in per-DOF computations and sums. |
| `uniform` | global or per-DOF read-only | Uniform random number in `[0, 1)`, refreshed per expression evaluation. |
| `gaussian` | global or per-DOF read-only | Standard normal random number, refreshed per expression evaluation. |

Context global parameters also appear as global variables in a bound `CustomIntegrator`, which enables algorithms using energy parameter derivatives or lambda dynamics.

## Minimal Constraint-Aware Verlet Pattern

Use this skeleton when implementing a basic custom dynamics step that respects context-state updates and constraints:

```python
integrator = openmm.CustomIntegrator(dt)
integrator.addPerDofVariable("x1", 0)
integrator.addUpdateContextState()
integrator.addComputePerDof("v", "v+0.5*dt*f/m")
integrator.addComputePerDof("x", "x+dt*v")
integrator.addComputePerDof("x1", "x")
integrator.addConstrainPositions()
integrator.addComputePerDof("v", "v+0.5*dt*f/m+(x-x1)/dt")
integrator.addConstrainVelocities()
```

Key points:

- `addUpdateContextState()` gives barostats, thermostats, and other forces a chance to update context state; put it once per outer step unless the algorithm intentionally differs.
- Save old positions before `addConstrainPositions()` so constrained displacement can be reflected back into velocities.
- Set `integrator.setConstraintTolerance(value)` when testing constrained systems.
- Use `setKineticEnergyExpression()` if the velocity stored in the context is offset from the on-step velocity used for reporting.

## Multiple Time Step Pattern

OpenMM force groups are the native way to evaluate fast and slow forces at different rates. Assign groups first, then build an integrator using `f0`, `f1`, or use OpenMM's `MTSIntegrator`/`MTSLangevinIntegrator` wrappers.

```python
for force in system.getForces():
    force.setForceGroup(0)
slow_force.setForceGroup(1)

integrator = openmm.CustomIntegrator(4*unit.femtoseconds)
integrator.addComputePerDof("v", "v+0.5*dt*f1/m")
for _ in range(4):
    integrator.addComputePerDof("v", "v+0.5*(dt/4)*f0/m")
    integrator.addComputePerDof("x", "x+(dt/4)*v")
    integrator.addComputePerDof("v", "v+0.5*(dt/4)*f0/m")
integrator.addComputePerDof("v", "v+0.5*dt*f1/m")
```

When using the bundled MTS wrappers:

- `MTSIntegrator(dt, [(group, frequency), ...])` and `MTSLangevinIntegrator(temperature, friction, dt, groups)` sort groups by frequency.
- Every frequency must be an integer multiple of the previous frequency after sorting; otherwise construction raises `ValueError`.
- Force group indices must be between 0 and 31.
- For PME, a common pattern is direct-space nonbonded in one group and reciprocal-space nonbonded in another via `NonbondedForce.setReciprocalSpaceForceGroup(group)`.

## Force-Group Energy Algorithms

For algorithms such as accelerated MD, query group-specific energy or force variables inside the integrator:

```python
integrator.addGlobalVariable("groupEnergy", 0)
integrator.addPerDofVariable("fg", 0)
integrator.addComputeGlobal("groupEnergy", "energy1")
integrator.addComputePerDof("fg", "f1")
integrator.addComputePerDof(
    "v",
    "v+dt*fprime/m; fprime=fother+fg*scale; fother=f-fg; scale=alpha/(alpha+E-groupEnergy)"
)
```

Rules:

- One computation step may reference only one force variable (`f`, `f0`, `f1`, ...) or one energy variable (`energy`, `energy0`, `energy1`, ...).
- Split computations into multiple steps if an expression would otherwise combine group variables illegally.
- Validate boosted/group algorithms by comparing `context.getState(getEnergy=True, groups={group})` to the integrator's expected group-energy term on a tiny system.

## Stochastic Integrator Notes

- Use `uniform` for accept/reject decisions and `gaussian` for Langevin/Brownian noise. If `uniform` or `gaussian` appears twice in one expression, the same sampled value is reused within that expression.
- For per-DOF expressions, random variables are sampled independently for every degree of freedom.
- Set a random seed on stochastic integrators when reproducibility matters, but do not assume bitwise-identical trajectories across platforms unless the target platform documents it.
- Test statistical behavior with tolerances and averages, not exact single-trajectory values.

## Flow Control

- Use `beginIfBlock(condition)`, `beginWhileBlock(condition)`, and `endBlock()` for global control flow.
- Conditions are global expressions only; they cannot depend directly on per-DOF variables except through values previously reduced with `addComputeSum()`.
- A `while` block can create an infinite loop. Include a counter or convergence guard when using it for minimization, MC retry, or adaptive algorithms.
- OpenMM validates block balance; a missing or unexpected `endBlock()` raises a CustomIntegrator error.

## Custom Variables and Runtime Updates

- Define persistent globals with `addGlobalVariable(name, initial_value)` and persistent per-DOF arrays with `addPerDofVariable(name, initial_value)`.
- Inspect or change globals with `getGlobalVariableByName()` and `setGlobalVariableByName()` in Python when implementing adaptive algorithms.
- For per-DOF variables, use `getPerDofVariableByName()` and `setPerDofVariableByName()` with one `Vec3` per particle.
- Keep variable names distinct from built-ins (`x`, `v`, `f`, `m`, `dt`, `energy`, `uniform`, `gaussian`) and custom force global parameter names unless deliberately sharing context parameters.

## Validation Checklist

1. Run one or a few steps on the `Reference` platform with simple masses, positions, and forces.
2. Check positions, velocities, constraints, and finite energies after each step for a tiny system.
3. If using groups, query each group independently with `Context.getState(..., groups={i})`.
4. If using stochastic terms, set seeds and assert distribution-level behavior.
5. Serialize and deserialize the integrator if it must be checkpointed or reused.
6. Run the same tiny validation with `CPU`, `CUDA`, `OpenCL`, or `HIP` only after `Reference` behavior is correct.
