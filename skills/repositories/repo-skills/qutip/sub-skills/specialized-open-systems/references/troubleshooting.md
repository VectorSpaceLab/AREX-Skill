# Specialized open-system troubleshooting

## Dicke basis versus full Hilbert space

- PIQS uses symmetry-reduced Dicke-basis dimensions, not always the full `2**N` space.
- Check `num_dicke_states(N)` before interpreting matrix shape.
- If a Hamiltonian dimension does not match the PIQS system, rebuild it with `jspin(N, basis='dicke')` or another Dicke-basis helper.

## Environment models

- Environment functions should accept both numbers and arrays.
- Spectral densities are expected to be real and zero for negative frequencies in the standard bosonic environment tests.
- Correlation functions can be complex; do not force them to real numbers unless the model says the imaginary part should vanish.

## HEOM cost control

- HEOM runtime grows quickly with system dimension, bath count, exponent count, and hierarchy depth.
- Validate bath objects and exponent counts before suggesting a full solve.
- Use very small `Nk` and `max_depth` in smoke examples.

## Optional acceleration

- MKL can accelerate some sparse linear-algebra paths, but the standard SciPy path remains valid without it.
- Treat optional acceleration as a performance decision, not as required correctness evidence.

## When to switch subskills

- Use `dynamics-and-solvers` for ordinary `mesolve`, `steadystate`, correlation, or Floquet workflows.
- Use `analysis-and-io` if the problem is only about plotting or saving the output of an open-system workflow.
