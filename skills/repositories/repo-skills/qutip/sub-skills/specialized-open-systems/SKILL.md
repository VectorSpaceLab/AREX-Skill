---
name: "specialized-open-systems"
description: "QuTiP PIQS, HEOM, environment, Bloch-Redfield, and non-Markovian workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Specialized open systems

Use this subskill when the task is about QuTiP's higher-level open-system model families, especially bath/environment construction, PIQS, HEOM, Bloch-Redfield, or non-Markovian transfer-tensor workflows.

## Read this subskill when the prompt mentions

- PIQS, `Dicke`, permutational invariance, collective emission, collective pumping, or Dicke basis states
- HEOM, hierarchical equations of motion, Drude-Lorentz baths, Lorentzian baths, bath exponents, or hierarchy depth
- `BosonicEnvironment`, `FermionicEnvironment`, `DrudeLorentzEnvironment`, `OhmicEnvironment`, spectral density, correlation function, or power spectrum
- Bloch-Redfield, `brmesolve`, bath coupling operators, or non-Markovian transfer-tensor methods

## What to decide first

1. Is the user asking for a bath/environment object, a solver, or a symmetry-reduced state representation?
2. Does the workflow stay in the Dicke basis or require the full Hilbert space?
3. Is the requested bath model bosonic, fermionic, Drude-Lorentz, Lorentzian, Ohmic, under-damped, or custom exponent based?
4. Is a small CPU example enough, or is the task asking for large-scale physics that needs a performance warning?

## Core workflow

- Use `qutip.core.environment` for spectral-density, correlation-function, and power-spectrum objects.
- Use `qutip.solver.heom` for HEOM baths and `HEOMSolver` when the hierarchy is part of the model.
- Use `qutip.piqs.piqs` for Dicke-basis states, collective spin operators, and the `Dicke` system wrapper.
- Return to `dynamics-and-solvers` when the task is only a generic `mesolve`, `steadystate`, or correlation calculation.

## Typical success signals

- Environment functions accept both scalars and arrays.
- Dicke-basis dimensions match the expected `num_dicke_states(N)` rather than the full `2**N` space.
- HEOM bath exponent counts and hierarchy depth are explicit before launching a solve.
- Optional acceleration is treated as a performance feature, not a correctness requirement.

## Boundaries

Use this subskill for advanced open-system model construction. Do not use it as the main route for:

- Generic `Qobj` algebra before the bath or symmetry model is defined; start in `core-objects`.
- Plain `mesolve`, `sesolve`, or `steadystate` questions with no specialized bath or PIQS/HEOM term; use `dynamics-and-solvers`.
- Plotting or serializing final states; use `analysis-and-io` after the model result exists.

## Answer shape

When responding from this subskill, give:

1. The model family: environment, HEOM, PIQS, Bloch-Redfield, or transfer tensor.
2. The required parameters and their physical meaning.
3. A tiny construction or validation snippet before any expensive solve.
4. The dimensionality or exponent-count check that bounds the cost.
5. Any optional acceleration or unavailable-backend note.

## Validation hints

- For PIQS, compare dimensions against `num_dicke_states(N)`.
- For environments, evaluate spectral density or correlation functions on both scalars and small arrays.
- For HEOM, print bath exponent counts and use small `Nk` / hierarchy depth in examples.

## Reference files

- `references/api-reference.md` for environment, PIQS, HEOM, and non-Markovian entry points.
- `references/workflows.md` for compact environment and PIQS examples.
- `references/troubleshooting.md` for basis, bath, and hierarchy pitfalls.

## Helper script

- `scripts/open_systems_smoke.py` constructs a Drude-Lorentz environment, a PIQS Dicke-basis object, and a small HEOM bath without launching an expensive solve.
