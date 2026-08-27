# Analysis and I/O troubleshooting

## Matplotlib and headless runs

- Install the `graphics` extra or install Matplotlib separately before using plotting helpers.
- In headless environments, call `matplotlib.use('Agg')` before importing plotting functions that create figures.
- Always close or save figures in scripts to avoid leaking GUI state.

## Basis-label and shape problems

- Errors like `got 1 ticklabels but needed 5` mean that `x_basis` or `y_basis` has the wrong length for the matrix being plotted.
- `All inputs should have the same shape.` means an animation or list-based plot received incompatible objects.
- Hinton plots expect operators or supported superoperators, not arbitrary state vectors.

## Bloch geometry

- Bloch arcs require distinct points on the same sphere.
- Errors about origin, opposite points, or different spheres are geometry problems, not Matplotlib problems.
- Use qubit kets or density matrices for `add_states`; higher-dimensional states need another visualization.

## Wigner and quasi-probability calculations

- Make the `xvec` and `yvec` grids explicit.
- Large grids or high-dimensional states can be slow; start with a small grid for diagnostics.
- Keep complex phase-space values and normalization conventions straight before plotting.

## File I/O

- `qsave` appends `.qu`; do not accidentally look for the unsuffixed path.
- Use a temporary directory for tests and scratch files.
- Use `file_data_store` and `file_data_read` for raw numeric arrays rather than QuTiP object serialization.

## Reporting helpers

- `about()` prints the active interpreter's package state; run it in the same environment as the failing workflow.
- `qutip.qip` is an external family package route. Install `qutip-qip` if the user truly needs quantum-information-processing circuit helpers.
